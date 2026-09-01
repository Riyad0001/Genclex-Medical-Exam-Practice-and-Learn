from apps.core_learning.models import LearningProgress, LearningCategory

from .serializers import LearningCategorySerializer

# calculate progress percentage for each category
def calculate_category_progress(user, category):
    total_contents = category.contents.filter(is_active=True).count()

    total_completed = LearningProgress.objects.filter(
        user=user, content__category=category, is_completed=True
    ).count()

    progress_percentage = (
        round((total_completed / total_contents) * 100) if total_contents else 0
    )

    return {
        "total_contents": total_contents,
        "completed_contents": total_completed,
        "progress_percentage": f"{progress_percentage}%",
    }


def get_category_items(category_id):
    """GET ALL THE CONTENT FROM LEARNING SYSTEM"""

    category = LearningCategory.objects.get(id=category_id)
    serializers = LearningCategorySerializer(category)
    return serializers.data

def get_single_learning_content(category_id, content_id):
    pass