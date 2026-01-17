# AIRA-Humanoid-Robot
AIRA (Advanced Interactive Robotic Assistant) is a semi-autonomous humanoid robot designed for intelligent interaction, perception, and safe service in real-world environments.
AIRA is a *semi-autonomous humanoid robotic assistant* designed to interact intelligently with humans using *offline artificial intelligence, **bilingual speech interaction, **vision-based perception, and **safe motion control*.  
The project is developed as a *college-level robotics innovation, with a strong focus on **modularity, safety, privacy, and real-world applicability, especially in the context of **Nepali society*.

AIRA demonstrates how modern AI systems (LLMs, speech, vision) can be *integrated responsibly into robotics* without relying entirely on cloud services.

---

## 🌟 Motivation & Problem Statement

Most humanoid and service robots today:
- Depend heavily on *cloud-based AI*
- Suffer from *high latency and privacy concerns*
- Are difficult to adapt to *local languages and environments*
- Lack clear *safety separation* between intelligence and motion

AIRA addresses these challenges by introducing an *offline-first, semi-autonomous architecture* that:
- Works without continuous internet
- Supports *English and Nepali*
- Separates decision-making from physical actuation
- Prioritizes *human safety and ethical control*

---

## 🎯 Project Objectives

- Design a *semi-autonomous humanoid robot* suitable for real-world service tasks
- Enable *natural human–robot interaction* using voice and expressions
- Implement *offline AI reasoning* using a local LLM
- Integrate *vision-based perception* for environment awareness
- Ensure *safe and controlled motion* using rule-based logic
- Build a *scalable software architecture* ready for hardware integration

---

## 🤖 Key Features

### 🧠 Offline Intelligence
- Local Large Language Model (LLM) running on PC/workstation
- No direct LLM-to-motor control (safety-first design)
- Structured intent extraction using JSON-based outputs

### 🗣️ Speech Interaction
- Wake-word based activation (hands-free operation)
- Offline Speech-to-Text (STT)
- Offline Text-to-Speech (TTS)
- Bilingual communication: *English & Nepali*

### 👁️ Vision & Perception
- Camera-based person and object detection
- On-demand visual observation (resource-efficient)
- Vision used only when required by task intent

### 🦾 Motion & Safety
- Predefined servo and movement sequences
- Sensor-based collision avoidance
- Rule-based safety constraints
- Human-in-the-loop execution

### 🎭 Expressions & Feedback
- Screen-based facial expressions
- State-based behavior (sleep, listening, thinking, speaking)
- Head gestures for yes/no responses

---

## 🧩 System Architecture Overview

AIRA follows a *layered, modular, and safety-oriented architecture*.

### High-Level Flow:
1. Wake-word detection
2. Speech-to-text conversion
3. Intent understanding via offline LLM
4. Task / skill routing
5. Vision and sensor verification (if required)
6. Safe motion execution
7. Voice and visual feedback to user

### Core Design Principle:
> *The LLM decides *what to do, but never how to move.**

---

## 🧠 Intelligence Design (LLM Role)

The LLM in AIRA:
- Understands user intent
- Extracts structured commands
- Determines whether vision or external data is required
- Responds in the same language as the user

Example LLM Output:
```json
{
  "intent": "GIVE_OBJECT",
  "object": "chocolate",
  "target": "person",
  "requires_vision": true,
  "safe_distance_cm": 60
}
