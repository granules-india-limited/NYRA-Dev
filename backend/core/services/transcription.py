import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from core.utils.logger import logger
from core.utils.auth_utils import verify_and_get_user_id_from_jwt

router = APIRouter(tags=["transcription"])

class TranscriptionResponse(BaseModel):
    text: str

@router.post("/transcription", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    user_id: str = Depends(verify_and_get_user_id_from_jwt)
):
    """Transcribe audio file to text using api.nyra-team.com/v1 endpoint."""
    try:
        # Validate file type - common audio formats
        allowed_types = [
            'audio/mp3', 'audio/mpeg', 'audio/mp4', 'audio/m4a', 
            'audio/wav', 'audio/webm', 'audio/mpga',
            'audio/x-m4a', 'audio/x-mp4', 'audio/x-wav', 'audio/x-webm'
        ]
        
        logger.debug(f"Received audio file: {audio_file.filename}, content_type: {audio_file.content_type}")
        
        if audio_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {audio_file.content_type}. Supported types: {', '.join(allowed_types)}"
            )
        
        # Check file size (25MB limit)
        content = await audio_file.read()
        if len(content) > 25 * 1024 * 1024:  # 25MB
            raise HTTPException(status_code=400, detail="File size exceeds 25MB limit")
        
        # Reset file pointer
        await audio_file.seek(0)
        
        # Call api.nyra-team.com/v1 transcription endpoint
        transcription_url = "https://api.nyra-team.com/v1/transcription"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {
                'audio_file': (audio_file.filename or 'audio.webm', content, audio_file.content_type)
            }
            
            try:
                response = await client.post(transcription_url, files=files)
                response.raise_for_status()
                
                # Parse response - assuming it returns JSON with 'text' field
                result = response.json()
                transcription_text = result.get('text', '') if isinstance(result, dict) else str(result)
                
                logger.debug(f"Successfully transcribed audio for user {user_id}")
                return TranscriptionResponse(text=transcription_text)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Transcription API returned error: {e.response.status_code} - {e.response.text}")
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Transcription API error: {e.response.text}"
                )
            except httpx.RequestError as e:
                logger.error(f"Failed to connect to transcription API: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Transcription service unavailable: {str(e)}"
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}") 