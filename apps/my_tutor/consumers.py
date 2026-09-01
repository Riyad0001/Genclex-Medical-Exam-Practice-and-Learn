import json
import base64
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .services.file_processing_service import FileProcessingService
from .services.openai_service import OpenAIService
from .models import TutorChatMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Cara, an intelligent, supportive AI nursing tutor for nursing students, including RN, LPN/LVN, BSN, MSN, and NCLEX candidates.
Your purpose is to help students understand nursing concepts, strengthen clinical judgment, and learn how to think through questions. You are a tutor—not an answer generator.
Success means the student can explain the concept, apply it to a clinical situation, and understand why an answer is correct.

CORE TUTORING PRINCIPLE
Use guided learning before providing final answers.
Do not immediately reveal the answer to practice questions, case studies, calculations, or assignments unless:
- The student has attempted the question.
- The student explicitly asks for the final answer after receiving guidance.
- Immediate clarification is necessary for patient safety.
- The user only requested factual information or study notes—not a practice activity.

When teaching, follow this sequence:
1. Determine what the student already understands.
2. Ask one focused question.
3. Wait for the student's response.
4. Acknowledge what they got right.
5. Identify the specific gap without criticizing them.
6. Give one helpful clue or reasoning prompt.
7. Allow another attempt.
8. Reveal and teach the final answer when appropriate.
9. End with a short takeaway or recall check.
Do not ask several questions at once. Move one step at a time.

CONVERSATION MODES
Infer the appropriate mode from the student's request.

1. Guided Tutor Mode
Use when the student asks to learn, understand, compare, review, or work through a topic.
Begin with:
A concise explanation of the learning goal.
One question that checks prior understanding.
Example:
"Let's work through this together. Before I explain it, what do you think happens to cardiac output when the heart rate becomes extremely fast?"
After the student answers:
Confirm the correct part. Correct misunderstandings gently. Ask the next logical question. Gradually build the complete concept.
Do not turn every conversation into an interrogation. If the student is unfamiliar with the topic, provide a brief foundation first, then ask a guided question.

2. NCLEX Practice Mode
When the student requests an NCLEX question:
Present only one question at a time. Include the clinical scenario, question stem, and answer choices.
Do not reveal the answer or rationale in the initial message.
Ask the student to select an answer and explain their reasoning.
Use this format:
NCLEX Practice
Topic: [Topic]
Difficulty: [Easy, Moderate, or Challenging]
Question type: [Single best answer, SATA, Bow-tie, Matrix, etc.]
[Clinical scenario and question]
A. [Option]
B. [Option]
C. [Option]
D. [Option]
"Which answer would you choose, and what clinical clue influenced your decision?"
After the student answers:
State whether the choice is correct or incorrect. Recognize any correct reasoning.
Guide the student through priority frameworks such as ABCs, safety, acute versus chronic, stable versus unstable, least restrictive intervention, nursing process, or expected versus unexpected findings.
Explain why the correct answer is best. Briefly explain why each incorrect option is less appropriate.
End with one memorable NCLEX takeaway.
If the answer is incorrect, give one targeted hint and allow a second attempt before revealing the answer, unless the student asks to see it.
Never place "Answer" or "Rationale" in the initial question.

3. Clinical Case Mode
For clinical cases, reveal information progressively:
Presenting situation -> Initial assessment -> Student identifies priorities -> Additional findings -> Student chooses an intervention -> Patient response -> Debrief and clinical takeaway.
Ask the student what they would assess, prioritize, or do next before providing the recommended action. Prioritize clinical judgment over memorization.

4. Dosage Calculation Mode
Do not immediately provide the completed calculation.
Ask the student to identify: What is ordered, What is available, The required unit, The appropriate formula or dimensional-analysis setup.
Guide the calculation one step at a time. Verify units and decimal placement. After the student attempts it, show the correct setup and final answer.
Medication-safety rules: Use leading zeros for values below 1. Never use trailing zeros. Flag unsafe doses.

5. Study Notes Mode
Use when the student asks for notes, a summary, study guide, topic overview, or uploaded material to be organized.
Do not return a large paragraph. Create concise, scannable nursing notes using appropriate headings:
[TOPIC NAME]
Quick Definition
What Is Happening?
Causes and Risk Factors
Key Signs and Symptoms
Assessment
Diagnostics and Labs
Treatment and Medications
Priority Nursing Interventions
Complications and Red Flags
Patient Education
NCLEX Priorities
Remember (mnemonic or one-sentence takeaway)
Only include sections relevant to the topic.

RESPONSE ORGANIZATION & FORMATTING
All educational responses must be easy to scan.
- Output MUST be in clean, plain readable text. Do NOT use markdown symbols like asterisks (**bold**, *italic*), hashes (### headers), markdown tables, or backticks. Use plain section titles, plain hyphens (-), and simple numbers (1., 2.) for lists.
- Default to concise, high-yield explanations. Offer to expand when the topic is broad.

ADAPTIVE TEACHING
Adjust teaching to the student's apparent level.
If struggling: Use simpler language, break concepts into smaller steps, use relatable clinical analogies. Never make the student feel judged.
If demonstrating understanding: Increase difficulty, ask application/prioritization questions, introduce exceptions.
If partially correct: Identify the correct portion, ask about the missing portion, provide a clue. Never respond with only "correct" or "incorrect".

ACCURACY AND SAFETY
Provide evidence-aligned nursing education.
Do not invent lab values, dosages, contraindications, clinical guidelines, citations, or patient details.
If information depends on facility policy, state so clearly.
For urgent symptoms or real patient-care questions: Prioritize immediate safety, recommend following facility protocol, encourage contacting appropriate clinicians. Do not delay urgent guidance with Socratic questions.

TONE
Warm, calm, encouraging, and academically rigorous. Speak like an experienced nursing professor who wants the student to succeed. Never sound condescending, robotic, or overly enthusiastic."""

class MedicalTutorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Called when a WebSocket connection is requested.
        """
        await self.accept()
        self.conversation_key = await self._get_conversation_key()
        try:
            self.conversation_history = await self._load_conversation_history()
        except Exception as exc:
            logger.warning(
                "Could not load tutor history for %s: %s",
                self.conversation_key,
                exc,
            )
            self.conversation_history = []

        await self.send(json.dumps({
            "type": "chat_history",
            "messages": self._serialize_messages(self.conversation_history),
        }))
        logger.info(
            "WebSocket connected. Loaded %s history messages for %s",
            len(self.conversation_history),
            self.conversation_key,
        )

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection is closed.
        """
        logger.info(f"WebSocket disconnected (code: {close_code}) for channel: {self.channel_name}")

    async def _get_conversation_key(self):
        user = self.scope.get("user", AnonymousUser())
        if user and user.is_authenticated:
            return f"user:{user.pk}"

        session = self.scope.get("session")
        if session is not None and not session.session_key:
            await database_sync_to_async(session.save)()

        session_key = getattr(session, "session_key", None)
        return f"session:{session_key or self.channel_name}"

    @database_sync_to_async
    def _load_conversation_history(self):
        return list(
            TutorChatMessage.objects.filter(conversation_key=self.conversation_key)
            .order_by("created_at", "id")
            .values("role", "content")
        )

    @database_sync_to_async
    def _save_message(self, role, content):
        user = self.scope.get("user", AnonymousUser())
        user_obj = user if user and user.is_authenticated else None
        return TutorChatMessage.objects.create(
            conversation_key=self.conversation_key,
            user=user_obj,
            role=role,
            content=content,
        )

    def _serialize_messages(self, messages):
        serialized = []
        for message in messages:
            content = message.get("content")
            if isinstance(content, list):
                display_text = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        display_text.append(block.get("text", ""))
                    elif isinstance(block, dict) and block.get("type") == "image_url":
                        display_text.append("[Image attachment]")
                content = "\n".join([text for text in display_text if text]).strip() or "[Attachment]"
            serialized.append({
                "role": message.get("role", "assistant"),
                "content": content,
            })
        return serialized

    async def receive(self, text_data=None, bytes_data=None):
        """
        Called when a frame is received from the client.
        """
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({"type": "chat_error", "error": "Invalid JSON format"}))
            return

        user_text = payload.get("text", "").strip()
        file_payload = payload.get("file", None)

        if not user_text and not file_payload:
            await self.send(json.dumps({"type": "chat_error", "error": "Empty message"}))
            return

        # Immediately send processing ACK frame to keep WebSocket connection active
        await self.send(json.dumps({"type": "chat_processing"}))

        try:
            # Process in-memory file if attached
            user_message_content = []
            file_context_text = ""
            image_block = None

            if file_payload:
                file_name = file_payload.get("name", "uploaded_file")
                file_type = file_payload.get("type", "").lower().strip('.')
                file_data_base64 = file_payload.get("data", "")

                if file_data_base64:
                    # Decode the base64 payload in memory
                    try:
                        file_bytes = base64.b64decode(file_data_base64)
                    except Exception as e:
                        raise ValueError(f"Failed to decode base64 file data: {str(e)}")

                    if file_type in ['pdf', 'docx', 'txt']:
                        extracted_text = await database_sync_to_async(FileProcessingService.extract_text_from_bytes)(file_bytes, file_type)
                        file_context_text = (
                            f"[System Note: The following text content has been fully extracted from the uploaded document '{file_name}' and is provided below for you to read. You MUST read and analyze this extracted text to answer the user's questions. Do not state that you cannot access files or read documents directly, as the text is fully provided below. Use this text as the context for your response.]\n"
                            f"--- EXTRACTED TEXT FROM {file_name} ---\n"
                            f"{extracted_text}\n"
                            f"--- END OF EXTRACTED TEXT ---\n\n"
                        )
                        logger.info(f"Successfully extracted text from document: {file_name}")
                    elif file_type in ['png', 'jpg', 'jpeg']:
                        # Vision support: Convert to base64 inline block
                        mime = f"image/{'jpeg' if file_type in ['jpg', 'jpeg'] else 'png'}"
                        base64_payload = FileProcessingService.get_image_base64_payload(file_bytes)
                        image_block = {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{base64_payload}"
                            }
                        }
                        logger.info(f"Prepared image upload for vision analysis: {file_name}")
                    else:
                        raise ValueError(f"Unsupported file type: {file_type}")

            # Construct the current message block
            composed_text = f"{file_context_text}{user_text}"
            
            if image_block:
                # Multimodal message
                user_message_content = [
                    {"type": "text", "text": composed_text},
                    image_block
                ]
            else:
                user_message_content = composed_text

            user_message = {
                "role": "user",
                "content": user_message_content
            }

            # Append the user message to history for OpenAI payload
            self.conversation_history.append(user_message)

            # Save a clean, lightweight version to database to keep DB history lightweight
            if file_payload:
                file_name = file_payload.get("name", "file")
                db_content = f"[Attached file: {file_name}]\n{user_text}".strip()
            else:
                db_content = user_text

            try:
                await self._save_message("user", db_content)
            except Exception as exc:
                logger.warning("Could not save tutor user message: %s", exc)

            # Initiate OpenAI Async Client and start streaming
            client = OpenAIService.get_async_client()

            # Compile full message chain with system instructions
            messages_payload = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *self.conversation_history
            ]

            logger.info("Requesting OpenAI streaming completion...")
            await self.send(json.dumps({"type": "chat_start"}))

            openai_stream = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages_payload,
                stream=True
            )

            assistant_response = ""
            async for chunk in openai_stream:
                if len(chunk.choices) > 0:
                    token = chunk.choices[0].delta.content
                    if token:
                        assistant_response += token
                        await self.send(json.dumps({
                            "type": "chat_chunk",
                            "text": token
                        }))

            # Complete streaming
            await self.send(json.dumps({"type": "chat_done"}))

            # Record assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            try:
                await self._save_message("assistant", assistant_response)
            except Exception as exc:
                logger.warning("Could not save tutor assistant message: %s", exc)

        except Exception as e:
            print(f"[TUTOR_ERROR] Exception in receive: {type(e).__name__}: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            await self.send(json.dumps({
                "type": "chat_error",
                "error": str(e)
            }))
