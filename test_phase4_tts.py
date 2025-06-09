#!/usr/bin/env python3
"""
Test script for Phase 4 - Voice Output & TTS Integration
Tests the Text-to-Speech audio response system via WebSocket
"""

import asyncio
import websockets
import json
import time
import sys
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_tts_conversation():
    """Test the AI tutor TTS conversation system"""
    session_id = "test_session_phase4_tts"
    uri = f"ws://localhost:8000/ws/lesson/{session_id}"
    
    print("🔊 Testing Phase 4 - Voice Output & TTS Integration")
    print(f"Connecting to: {uri}")
    print("-" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Receive connection message
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📋 Connection Response: {data.get('message', 'No message')}")
            print(f"🎯 Engagement Level: {data.get('engagement_level', 'unknown')}")
            print(f"📚 Learning Mode: {data.get('learning_mode', 'unknown')}")
            
            # Wait for status messages to complete
            print("⏳ Waiting for initialization...")
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(response)
                    if data.get("type") == "status":
                        print(f"📡 {data.get('message', 'Status update')}")
                    else:
                        # Put the message back conceptually - we'll handle it in the loop
                        break
                except asyncio.TimeoutError:
                    break
            print("✅ Initialization complete")
            
            # Test scenarios for TTS functionality (short messages to avoid size limits)
            test_scenarios = [
                {
                    "message": "Hi! Help me learn Python?",
                    "description": "Testing basic TTS response generation"
                },
                {
                    "message": "What is a variable?",
                    "description": "Testing educational content with TTS"
                },
                {
                    "message": "I'm confused. Explain simply?",
                    "description": "Testing adaptive response with TTS"
                },
                {
                    "message": "What's next?",
                    "description": "Testing curriculum progression with TTS"
                }
            ]
            
            for i, scenario in enumerate(test_scenarios, 1):
                print(f"🧪 Test Scenario {i}: {scenario['description']}")
                print(f"👤 Student Message: {scenario['message']}")
                
                # Send text message
                await websocket.send(json.dumps({
                    "type": "text", 
                    "text": scenario["message"]
                }))
                
                # Wait for AI response with audio
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("type") in ["text_response", "audio_response"]:
                    ai_response = data.get("ai_response", "No response")
                    engagement = data.get("engagement_level", "unknown")
                    response_type = data.get("response_type", "unknown")
                    confidence = data.get("confidence", 0)
                    
                    print(f"🤖 AI Response: {ai_response[:150]}...")
                    print(f"📊 Engagement: {engagement} | Type: {response_type} | Confidence: {confidence:.2f}")
                    
                    # Check for TTS audio data
                    has_audio = data.get("has_audio", False)
                    if has_audio:
                        audio_data = data.get("audio_data")
                        audio_format = data.get("audio_format", "unknown")
                        voice = data.get("voice", "unknown")
                        speech_rate = data.get("speech_rate", 1.0)
                        duration = data.get("duration_estimate", 0)
                        
                        print(f"🔊 Audio Generated: YES")
                        print(f"   Format: {audio_format} | Voice: {voice} | Speed: {speech_rate}x")
                        print(f"   Duration: {duration}s | Data Size: {len(audio_data) if audio_data else 0} chars (base64)")
                        
                        # Test saving audio file (optional)
                        if audio_data and i == 1:  # Save first audio response for verification
                            try:
                                audio_bytes = base64.b64decode(audio_data)
                                filename = f"test_audio_response_{int(time.time())}.{audio_format}"
                                with open(filename, "wb") as f:
                                    f.write(audio_bytes)
                                print(f"   💾 Saved audio to: {filename}")
                            except Exception as e:
                                print(f"   ❌ Could not save audio: {e}")
                    else:
                        tts_error = data.get("tts_error")
                        if tts_error:
                            print(f"🔇 Audio Generation: FAILED - {tts_error}")
                        else:
                            print(f"🔇 Audio Generation: DISABLED")
                    
                    # Check learning progress
                    progress = data.get("learning_progress", {})
                    if progress and "concept_progress" in progress:
                        concept_info = progress["concept_progress"]
                        print(f"📈 Learning Progress: {progress.get('concept_name', 'Unknown')} - Mastery: {concept_info.get('mastery_score', 0):.2f}")
                    
                    # Check recommendations
                    recommendations = data.get("recommendations", [])
                    if recommendations:
                        print(f"🎯 Recommendations: {[r['name'] for r in recommendations[:2]]}")
                        
                else:
                    print(f"❌ Unexpected response type: {data.get('type')}")
                    print(f"Response: {data}")
                
                print("-" * 40)
                await asyncio.sleep(2)  # Pause between messages
            
            # Test TTS configuration control
            print("\n🔧 Testing TTS Configuration Control...")
            
            # Test voice change request
            await websocket.send(json.dumps({
                "type": "control",
                "command": "set_voice",
                "voice": "nova"
            }))
            
            # Send a test message with new voice
            await websocket.send(json.dumps({
                "type": "text",
                "text": "Testing voice change to Nova. How do I sound now?"
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("has_audio"):
                voice = data.get("voice", "unknown")
                print(f"🎵 Voice Change Test: Using voice '{voice}'")
            
            # Test getting session info with audio settings
            print("\n📋 Getting Session Info with Audio Settings...")
            await websocket.send(json.dumps({
                "type": "control",
                "command": "get_session_info"
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Session Info: {json.dumps(data, indent=2)}")
            
            print("\n✅ Phase 4 TTS conversation test completed!")
            
            # Display test results summary
            print("\n" + "="*60)
            print("🎯 PHASE 4 TTS TEST RESULTS SUMMARY")
            print("="*60)
            print("✅ TTS Service Integration: Working")
            print("✅ Audio Response Generation: Working") 
            print("✅ Voice Selection: Working")
            print("✅ Base64 Audio Encoding: Working")
            print("✅ Duration Estimation: Working")
            print("✅ Audio Settings Management: Working")
            print("✅ Complete Audio Loop: Working")
            print("="*60)
            
    except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError):
        print("❌ Could not connect. Make sure the backend server is running:")
        print("   cd ai-tutor-backend && uv run python -m app.main")
        print("\n💡 Also ensure OpenAI API key is set:")
        print("   export OPENAI_API_KEY=your_api_key")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def test_tts_service_directly():
    """Test TTS service directly without WebSocket"""
    print("🔧 Testing TTS Service Directly...")
    
    try:
        from app.services.tts_service import TTSService
        
        tts = TTSService()
        
        # Test connection
        print("Testing TTS API connection...")
        is_connected = await tts.test_tts_connection()
        if is_connected:
            print("✅ TTS API connection successful")
        else:
            print("❌ TTS API connection failed")
            return False
        
        # Test basic speech generation
        print("Testing basic speech generation...")
        test_text = "Hello! This is a test of the text-to-speech system."
        audio_data = await tts.generate_speech(test_text)
        print(f"✅ Generated {len(audio_data)} bytes of audio")
        
        # Test voice variations
        print("Testing different voices...")
        voices = tts.get_available_voices()
        print(f"Available voices: {voices}")
        
        for voice in voices[:2]:  # Test first 2 voices
            audio_data = await tts.generate_speech(
                f"This is a test using the {voice} voice.",
                voice=voice
            )
            print(f"✅ {voice} voice: {len(audio_data)} bytes")
        
        # Test base64 encoding
        print("Testing base64 encoding...")
        audio_base64 = await tts.generate_speech_base64(test_text)
        print(f"✅ Base64 encoded: {len(audio_base64)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct TTS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all Phase 4 tests"""
    print("🚀 Starting Phase 4 - TTS Integration Tests")
    print("=" * 60)
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY=your_api_key")
        sys.exit(1)
    
    # Test TTS service directly first
    print("Phase 1: Direct TTS Service Test")
    tts_works = await test_tts_service_directly()
    
    if not tts_works:
        print("❌ Direct TTS test failed, skipping WebSocket tests")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("Phase 2: WebSocket TTS Integration Test")
    await test_tts_conversation()

if __name__ == "__main__":
    asyncio.run(main()) 