from random import shuffle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import CategorySerializer
from .models import Category, Sub_Category,  Question, Card, Progress


class CategoryContentAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        categories = Category.objects.prefetch_related(
            "subcategories__cards__questions"
        ).all()

        if not categories.exists():
            return Response({
                "success": False,
                "message": "No category found",
                "status": 404,
                "data": []
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(categories, many=True)

        return Response({
            "success": True,
            "message": "Request successful",
            "status": 200,
            "data": serializer.data
        }, status=status.HTTP_200_OK)




class AnswerSubmitAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user

        category_id = request.data.get("category_id")
        subcategory_id = request.data.get("subcategory_id")
        card_id = request.data.get("card_id")
        answers_data = request.data.get("answers", [])

        if not all([category_id, subcategory_id, card_id]):
            return Response({
                "success": False,
                "message": "category_id, subcategory_id, card_id required",
                "status": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            card = Card.objects.get(
                id=card_id,
                category_id=category_id,
                sub_category_id=subcategory_id
            )
        except Card.DoesNotExist:
            return Response({
                "success": False,
                "message": "Invalid category/subcategory/card relation",
                "status": 404
            }, status=status.HTTP_404_NOT_FOUND)

        easy_count = 0
        hard_count = 0
        results = []

        for item in answers_data:

            question_id = item.get("question_id")
            is_easy = item.get("is_easy", False)

            try:
                question = Question.objects.get(id=question_id, card=card)
            except Question.DoesNotExist:
                continue

            # question.is_easy = is_easy
            # question.save()

            obj, created = Progress.objects.get_or_create(
                user=user,
                question=question,
                defaults={
                    "is_easy": is_easy,
                    "is_hard": not is_easy,
                    "reviewed": True})

            if not created:
                obj.is_easy = is_easy
                obj.is_hard = not is_easy
                obj.reviewed = True
                obj.save()

            if is_easy:
                easy_count += 1
            else:
                hard_count += 1

            results.append({
                "question_id": question_id,
                "is_easy": is_easy
            })

        return Response({
            "success": True,
            "message": "Answers submitted successfully",
            "status": 200,
            "data": {
                "is_answer": {
                    "easy": easy_count,
                    "hard": hard_count
                },
                "results": results}
        }, status=status.HTTP_200_OK)

    
class FlashcardProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        categories = Category.objects.all()
        
        total_questions = Question.objects.count()
        progress_data = Progress.objects.filter(user=user)
        
        reviewed_count = progress_data.count()
        easy_count = progress_data.filter(is_easy=True).count()
        hard_count = progress_data.filter(is_hard=True).count()
        not_attempted = max(0, total_questions - reviewed_count)
        
        mastered_cards = progress_data.filter(is_easy=True).count()
        avg_recall = round((easy_count / reviewed_count * 100), 2) if reviewed_count > 0 else 0
        percentage = round((reviewed_count / total_questions * 100), 2) if total_questions > 0 else 0

        category_stats = []
        for cat in categories:
            cat_questions = Question.objects.filter(card__category=cat)
            total_cat_cards = cat_questions.count()
            cat_progress = progress_data.filter(question__card__category=cat)
            
            studied = cat_progress.count()
            e = cat_progress.filter(is_easy=True).count()
            h = cat_progress.filter(is_hard=True).count()
            not_att = max(0, total_cat_cards - studied)
            
            recall = round((e / studied * 100), 2) if studied > 0 else 0
            
            category_stats.append({
                "category_name": cat.name,
                "total_cards": total_cat_cards,
                "cards_studied": studied,
                "easy_count": e,
                "hard_count": h,
                "not_attempted": not_att,
                "recall_percent": recall,
                "mastered_count": e
            })

        return Response({
            "success": True,
            "data": {
                "overall": {
                    "easy": easy_count,
                    "hard": hard_count,
                    "not_attempted": not_attempted,
                    "percentage": percentage,
                    "cards_studied": reviewed_count,
                    "total_cards": total_questions,
                    "avg_recall": avg_recall,
                    "mastered_cards": mastered_cards
                },
                "categories": category_stats
            }
        })