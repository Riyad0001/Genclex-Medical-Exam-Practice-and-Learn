from rest_framework import serializers
from .models import (
    NCLEXQBank,
    NCLEXSubtopic,
    QuestionOption,
    NCLEXQuestion,
    NCLEXCategory,
    NCLEXTopic,
    PracticeSession,
)

class NCLEXAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            "id",
            "title",
            "order",
        ]


class NCLEXQuestionSerializer(serializers.ModelSerializer):
    explanation = serializers.SerializerMethodField()

    options = NCLEXAnswerSerializer(
        source="answers",
        many=True,
        read_only=True,
    )

    class Meta:
        model = NCLEXQuestion
        fields = [
            "id",
            "question",
            "type",
            "level",
            "note",
            # "avg_solve_percent",
            "explanation",
            "options",
            "passage",
        ]

    def get_explanation(self, obj):
        if self.context.get("mode") != "tutorial":
            return None

        request = self.context.get("request")

        if obj.explanation:
            return request.build_absolute_uri(obj.explanation.url)

        return None


class StartExamSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    subcategory_id = serializers.IntegerField(required=False, allow_null=True)
    mode = serializers.ChoiceField(choices=["tutorial", "test"])
    question_select = serializers.IntegerField(min_value=1)
    passage = serializers.CharField(required=False, allow_null=True)

    def validate(self, attrs):
        category_id = attrs.get("category_id")
        subcategory_id = attrs.get("subcategory_id")

        if category_id and subcategory_id:
            raise serializers.ValidationError(
                "Select either category_id or subcategory_id."
            )

        if not category_id and not subcategory_id:
            raise serializers.ValidationError(
                "category_id or subcategory_id is required."
            )

        return attrs


class SubmitAnswerSerializer(serializers.Serializer):
    exam_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    answer = serializers.JSONField()


class ExamSerializer(serializers.ModelSerializer):
    exam_type = serializers.SerializerMethodField()
    session_id = serializers.SerializerMethodField()
    total_answered = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()
    incorrect_answer = serializers.SerializerMethodField()

    class Meta:
        model = NCLEXQBank
        fields = [
            "id",
            "title",
            "subtitle",
            "exam_level",
            "exam_status",
            "total_questions",
            "total_time",
            "created_at",
            "completed_at",
            "session_id",
            "exam_type",
            "total_answered",
            "correct_answer",
            "incorrect_answer",
        ]

    def get_session_id(self, obj):
        session = obj.exam_sessions.first()
        return session.id if session else None

    def get_exam_type(self, obj):
        session = obj.exam_sessions.first()
        return session.exam_type if session else None

    def get_total_answered(self, obj):
        session = obj.exam_sessions.first()
        if not session:
            return 0
        return session.question_results.count()

    def get_correct_answer(self, obj):
        session = obj.exam_sessions.first()
        if not session:
            return 0
        return session.question_results.filter(is_correct=True).count()

    def get_incorrect_answer(self, obj):
        session = obj.exam_sessions.first()
        if not session:
            return 0
        return session.question_results.filter(
            is_correct=False, is_skipped=False
        ).count()


"""BADSHA - UPDATED API FOR NCLEX EXAM"""
class NCLEXPracticeSubtopicSerializer(serializers.ModelSerializer):
    total_question = serializers.IntegerField(read_only=True)

    class Meta:
        model = NCLEXSubtopic
        fields = ["id", "title", "total_question"]


class NCLEXPracticeTopicSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="title", read_only=True)
    total_subtopic = serializers.IntegerField(read_only=True)
    subtopic = NCLEXPracticeSubtopicSerializer(
        source="subtopics",
        many=True,
        read_only=True,
    )

    class Meta:
        model = NCLEXTopic
        fields = ["id", "topic_name", "total_subtopic", "subtopic"]


class NCLEXPracticeListSerializer(serializers.ModelSerializer):
    """Nested category, topic, and subtopic summary for NCLEX practice."""

    category = serializers.CharField(source="title", read_only=True)
    total_question = serializers.IntegerField(read_only=True)
    total_topic = serializers.IntegerField(read_only=True)
    topics = NCLEXPracticeTopicSerializer(many=True, read_only=True)

    class Meta:
        model = NCLEXCategory
        fields = ["category", "total_question", "total_topic", "topics"]


class PracticeSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeSession
        fields = ["id", "user", "total_question", "practice_mode", "topic", "subtopic", "created_at"]

        read_only_fields = ["id", "user", "created_at"]


class PracticeSessionCreateSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["tutorial", "test"])
    total_question = serializers.IntegerField(min_value=1)
    topic_id = serializers.IntegerField(required=False, allow_null=True)
    subtopic_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        topic_id = attrs.get("topic_id")
        subtopic_id = attrs.get("subtopic_id")

        if topic_id is None and subtopic_id is None:
            raise serializers.ValidationError(
                "Provide either topic_id or subtopic_id."
            )

        if topic_id is not None and subtopic_id is not None:
            raise serializers.ValidationError(
                "Provide either topic_id or subtopic_id, not both."
            )

        return attrs


class PracticeAnswerSubmitSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    answer = serializers.JSONField()


class NCLEXPracticeExamOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ["id", "text"]


class NCLEXPracticeExamQuestionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="question", read_only=True)
    topic = serializers.CharField(source="topic.title", read_only=True)
    subtopic = serializers.CharField(source="subtopic.title", read_only=True)
    unit = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()

    class Meta:
        model = NCLEXQuestion
        fields = [
            "id",
            "title",
            "topic",
            "subtopic",
            "type",
            "level",
            "note",
            "passage",
            "unit",
            "options",
        ]

    def get_unit(self, obj):
        return obj.metadata.get("unit") if obj.type == "input" else None

    def get_options(self, obj):
        # The single correct option is stored for input validation but must not
        # be shown to the user before submitting an answer.
        if obj.type == "input":
            return []
        return NCLEXPracticeExamOptionSerializer(obj.answers.all(), many=True).data


# =========================================================================
# NCLEX FINAL EXAM MODULE SERIALIZERS
# =========================================================================

class NCLEXExamItemSerializer(serializers.ModelSerializer):
    """User-aware serializer for the 5 NCLEX Final Exams listing."""
    status = serializers.SerializerMethodField()
    is_unlocked = serializers.SerializerMethodField()
    lock_message = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    readiness_level = serializers.SerializerMethodField()
    completed_date = serializers.SerializerMethodField()
    session_id = serializers.SerializerMethodField()
    remaining_seconds = serializers.SerializerMethodField()
    current_question_index = serializers.SerializerMethodField()
    can_start = serializers.SerializerMethodField()
    can_resume = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()

    class Meta:
        model = NCLEXQBank
        fields = [
            "id",
            "order",
            "title",
            "subtitle",
            "tag",
            "level",
            "total_question",
            "time_limit_mins",
            "status",
            "is_unlocked",
            "lock_message",
            "score",
            "readiness_level",
            "completed_date",
            "session_id",
            "remaining_seconds",
            "current_question_index",
            "can_start",
            "can_resume",
            "can_review",
        ]

    def _get_user_state(self, obj):
        user_states = self.context.get("user_states", {})
        return user_states.get(obj.id, {})

    def get_tag(self, obj):
        state = self._get_user_state(obj)
        if "tag" in state and state["tag"] is not None:
            return state["tag"]
        return obj.tag

    def get_status(self, obj):
        state = self._get_user_state(obj)
        return state.get("status", "locked")

    def get_is_unlocked(self, obj):
        state = self._get_user_state(obj)
        return state.get("is_unlocked", False)

    def get_lock_message(self, obj):
        state = self._get_user_state(obj)
        return state.get("lock_message")

    def get_score(self, obj):
        state = self._get_user_state(obj)
        return state.get("score")

    def get_readiness_level(self, obj):
        state = self._get_user_state(obj)
        return state.get("readiness_level")

    def get_completed_date(self, obj):
        state = self._get_user_state(obj)
        return state.get("completed_date")

    def get_session_id(self, obj):
        state = self._get_user_state(obj)
        return state.get("session_id")

    def get_remaining_seconds(self, obj):
        state = self._get_user_state(obj)
        return state.get("remaining_seconds")

    def get_current_question_index(self, obj):
        state = self._get_user_state(obj)
        return state.get("current_question_index", 0)

    def get_can_start(self, obj):
        state = self._get_user_state(obj)
        return state.get("can_start", False)

    def get_can_resume(self, obj):
        state = self._get_user_state(obj)
        return state.get("can_resume", False)

    def get_can_review(self, obj):
        state = self._get_user_state(obj)
        return state.get("can_review", False)


class NCLEXExamAnswerSubmitSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    answer = serializers.JSONField()
    current_index = serializers.IntegerField(required=False, default=0)


class NCLEXExamFlagSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    is_flagged = serializers.BooleanField()


