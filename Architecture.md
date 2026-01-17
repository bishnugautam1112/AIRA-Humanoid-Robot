---

## Layer-wise Architecture

---

### 1. Interaction Layer

**Purpose:**  
Handles all human–robot communication and expressive feedback.

**Responsibilities:**
- Wake-word detection
- Speech capture and playback
- Facial expressions and visual states
- Gesture feedback (head nodding)

**Technologies:**
- Wake Word: Porcupine / Custom keyword spotting
- Speech-to-Text: Whisper.cpp
- Text-to-Speech: Piper TTS
- UI & Expressions: Pygame / Tkinter
- Audio I/O: PyAudio

---

### 2. Intelligence Layer (AI Brain)

**Purpose:**  
Interprets user intent, reasons about tasks, and produces structured decisions.

**Responsibilities:**
- Natural language understanding
- Bilingual response generation (English & Nepali)
- Intent extraction in structured format
- Context handling (short-term)

**Design Rule:**  
The LLM **never controls hardware directly**.

**Technologies:**
- LLM Runtime: Ollama
- Models: Phi-3 / LLaMA-based models
- Prompt Engineering: JSON schema-based outputs
- Language Handling: Unicode-safe processing

**Example Output:**
```json
{
  "intent": "MOVE_AND_GIVE_OBJECT",
  "object": "chocolate",
  "target": "person",
  "requires_vision": true,
  "safety_priority": "high"
}
```
## 3. Skill & Task Layer

### Purpose
The Skill & Task Layer acts as a **bridge between intelligence and physical execution**.  
It converts structured intents from the Intelligence Layer into **validated, safe, and executable behaviors**.

This layer ensures that:
- Only **allowed actions** are executed
- Complex tasks are broken into **deterministic sub-steps**
- Failures are handled gracefully

---

### Responsibilities
- Validate AI-generated intents
- Select appropriate skill modules
- Sequence task execution
- Manage task states (start, running, completed, failed)
- Handle fallbacks and retries

---

### Example Skills
- `greet_user`
- `answer_question`
- `observe_environment`
- `move_to_person`
- `give_object`
- `nod_yes / nod_no`

Each skill is **predefined and bounded**, ensuring predictability.

---

### Technologies
- Python-based finite state machines (FSM)
- Rule-based task validation
- Event-driven execution model

---

## 4. Perception & Safety Layer

### Purpose
This layer provides **environmental awareness** and ensures **safe interaction with humans and surroundings**.

It operates **on-demand**, not continuously, to optimize computation and preserve privacy.

---

### Responsibilities
- Person detection and tracking
- Object detection (e.g., chocolate, bottle, tools)
- Distance estimation
- Obstacle detection
- Emergency stop conditions

---

### Vision System
- Camera is activated **only when required**
- Frames are captured temporarily and discarded after processing
- Vision results are converted into abstract facts (e.g., “person detected at 1.2m”)

---

### Sensor System
- Ultrasonic sensors for near-field obstacle detection
- Threshold-based collision avoidance
- Priority override over all motion commands

---

### Technologies
- OpenCV (image processing)
- YOLO (object & person detection)
- PyTorch (model inference)
- GPIO-based ultrasonic sensor drivers

---

## 5. Motion Control Layer

### Purpose
The Motion Control Layer is responsible for **all physical movement**, while strictly enforcing safety constraints.

This layer is **non-AI**, deterministic, and rule-based.

---

### Responsibilities
- Servo angle control (head, shoulder, elbow)
- Wheel motor control (forward, turn, stop)
- Motion smoothing and limits
- Collision avoidance responses
- Emergency halt

---

### Design Constraints
- Receives commands **only from Skill Layer**
- Executes **pre-approved motion patterns**
- Never interprets natural language
- No learning or adaptive behavior

---

### Motion Examples
- Head nodding for yes/no
- Arm extension to offer object
- Slow approach towards detected person
- Immediate stop on obstacle detection

---

### Technologies
- PWM-based servo control
- Motor drivers (L298N / equivalent)
- Python GPIO libraries
- Safety watchdog timers

---

## 6. Hardware Abstraction Layer (HAL)

### Purpose
The HAL ensures **hardware independence**, allowing the same software to run on:
- PC (simulation)
- Raspberry Pi (real robot)

---

### Responsibilities
- Abstract GPIO operations
- Normalize sensor data
- Provide mock interfaces for development
- Isolate hardware-specific code

---

### Benefits
- Faster software development before hardware arrival
- Easier hardware replacement
- Simplified testing and debugging

---

### Technologies
- Python abstraction classes
- Mock drivers for simulation
- Platform-specific adapters

---

## 7. Deployment Architecture

### Logical Deployment

PC / Workstation ├── Offline LLM (Ollama) ├── Vision Models (YOLO) └── High-level Reasoning

Raspberry Pi ├── Speech Modules ├── Skill & Task Layer ├── Motion Control └── Sensor Interfaces

---

### Communication
- Local network (Wi-Fi / Ethernet)
- REST API or Socket-based IPC
- JSON-based message exchange

---

## 8. Safety & Ethical Design

### Safety Measures
- Human-initiated commands only
- Rule-based motion limits
- Sensor-priority overrides
- Emergency stop capability

---

### Ethical Considerations
- No continuous surveillance
- Offline by default
- No autonomous goal generation
- Transparent and predictable behavior

---

## 9. Performance & Optimization Strategy

- Lazy-loading of AI models
- On-demand vision inference
- Lightweight IPC messages
- Predefined motion primitives
- Parallel handling of perception and motion

---

## 10. Extensibility & Future Work

Potential future enhancements:
- Autonomous task suggestion (with approval)
- Improved multimodal reasoning
- Multi-language expansion
- Simulation-based reinforcement learning
- Multi-robot coordination

---

## 11. Final Architectural Summary

AIRA’s architecture ensures:
- **Controlled autonomy**
- **Human safety**
- **Offline intelligence**
- **Clear separation of responsibilities**

> AIRA is intentionally designed as a **semi-autonomous humanoid system**, balancing intelligence with responsibility and real-world feasibility.

---
