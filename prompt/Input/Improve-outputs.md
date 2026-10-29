# PROJECT: BUDDY AI — CONVERSATIONAL INTELLIGENCE AND RETRIEVAL REFINEMENT

## 1. YOUR ROLE

You are a senior AI engineer, LLM application architect, conversational AI specialist, and software engineer.

Your task is to inspect, debug, and improve the existing Buddy AI agent in this repository.

Buddy is intended to be an intelligent, natural, context-aware AI assistant with knowledge of APCOER Pune, its faculty, departments, campus, and other relevant institutional information.

However, the current implementation exhibits serious conversational problems:

* It repeatedly introduces itself as a college receptionist.
* It incorrectly interprets follow-up messages.
* It redirects unrelated questions toward the college.
* It uses unnecessarily formal, scripted language.
* It appears to have problems retrieving relevant information.
* It exposes repetitive source-reference messages.
* It may have issues with pronunciation when its responses are spoken aloud.

We need to correct the underlying implementation rather than merely changing a few sentences in the system prompt.

IMPORTANT: Work with the existing project architecture. Do not rebuild the entire application unnecessarily.

---

## 2. MANDATORY FIRST STEP: CREATE A SEPARATE GIT BRANCH

Before modifying any files:

1. Inspect the current Git repository and working tree.

2. Identify the current branch.

3. Preserve any existing uncommitted changes.

4. Create and switch to a new feature branch named:

   `feature/buddy-conversation-intelligence`

5. Confirm that the new branch is active before proceeding.

6. Do not commit, overwrite, discard, or reset existing user changes.

7. Do not modify the production branch directly.

If the branch already exists, inspect its state and choose a safe approach without overwriting existing work.

After creating the branch, inspect the repository structure and identify the components responsible for:

* System prompts and agent instructions.
* LLM initialization and inference.
* Conversation history and session management.
* Retrieval-augmented generation (RAG).
* Document ingestion and knowledge storage.
* Web search or external information retrieval, if implemented.
* Source citations and source-count displays.
* Voice output and text-to-speech processing.
* Frontend chat rendering.
* Backend API endpoints and response formatting.
* Local model and offline operation, if supported.

Do not assume that these components exist under particular filenames. Discover the actual implementation.

---

## 3. DEFINE THE CORRECT IDENTITY OF BUDDY

Buddy must be a general-purpose conversational AI assistant with institutional knowledge of APCOER Pune.

It must not behave like a receptionist unless the user specifically requests receptionist-style assistance.

Its primary objective is to answer the user's actual question accurately, naturally, and directly.

### Required behavioral principles

A. Answer the user's actual question first.

B. Use APCOER-specific information when relevant.

C. Do not introduce APCOER into unrelated conversations.

D. Do not repeatedly introduce itself.

E. Maintain conversational context across follow-up messages.

F. Use natural, concise language.

G. Do not invent institutional facts.

H. Distinguish verified knowledge from assumptions and uncertainty.

I. Use retrieved sources when appropriate without allowing irrelevant retrieved information to override the user's request.

J. Remain helpful even when institutional information is unavailable.

### Replace the existing persona instructions if necessary

Review the existing system prompt and remove instructions that encourage Buddy to:

* Introduce itself at the beginning of every response.
* Call itself a receptionist in every conversation.
* Redirect every question toward APCOER.
* Ask whether the user wants to visit the college after unrelated answers.
* Use overly enthusiastic greetings repeatedly.
* Mention the institution when it is not relevant.
* Follow rigid response templates regardless of context.

Do not simply append a new prompt to an old conflicting prompt.

Identify and eliminate conflicting instructions throughout the prompt hierarchy, including system prompts, developer prompts, templates, and any additional persona instructions.

### Recommended system prompt

Use the following as the conceptual foundation. Adapt it to the existing architecture.

"You are Buddy, a helpful, intelligent, and conversational AI assistant.

Your purpose is to answer users' questions accurately, naturally, and directly. You have access to knowledge about APCOER Pune and may also answer general questions across a wide range of subjects.

You are not required to act as a receptionist. Mention APCOER only when it is relevant to the user's question or when the user explicitly asks about it.

Understand the current message in the context of the conversation. When the user provides a follow-up, interpret it using the preceding messages rather than treating it as an unrelated request.

Answer directly before providing optional explanations or asking follow-up questions.

Use concise, friendly, natural language. Avoid scripted introductions, repetitive greetings, excessive formality, and unnecessary promotional language.

When answering questions about APCOER, use relevant institutional information from the available knowledge base. When answering general questions, use your general knowledge and other supported information sources as appropriate.

Never invent faculty members, institutional policies, dates, locations, events, or source references.

If reliable information is unavailable, acknowledge the limitation and explain what information would help resolve the question.

Distinguish between information retrieved from institutional documents, general model knowledge, and externally verified current information.

Do not claim to have checked current records, verified facts, searched the internet, or consulted a directory unless the corresponding operation actually occurred.

When a user asks a straightforward question, provide the answer without unnecessary introductions or irrelevant follow-up questions.

You may ask a follow-up question when it genuinely helps clarify the user's intent.

Your primary responsibility is to help the user, not to promote the institution or keep the conversation restricted to institutional topics."

Implement this as a coherent prompt, not as an additional competing instruction layer.

---

## 4. FIX CONVERSATIONAL CONTEXT MANAGEMENT

This is one of the highest-priority requirements.

The following conversation currently fails:

User:
"What are places we should visit in Pune?"

Buddy:
"Hello! As the receptionist here at APCOER Pune, I would be delighted to share some wonderful spots..."

User:
"As I was planning to visit these places"

Buddy:
"Well, if you are planning to visit our campus here at APCOER Pune..."

The second answer is incorrect because the user is referring to the places previously discussed.

### Required behavior

Buddy must maintain an appropriate conversation history and resolve references such as:

* These places.
* Those locations.
* That professor.
* Tell me more.
* What about tomorrow?
* Is it nearby?
* Which one is better?
* Can you explain that?
* What about its history?

### Investigate the existing implementation

Determine whether the application:

1. Sends the previous conversation to the LLM.
2. Sends only the most recent user message.
3. Truncates the conversation history incorrectly.
4. Stores messages under the wrong session identifier.
5. Includes retrieved documents that dominate conversational context.
6. Rewrites follow-up messages using an incorrect query-rewriting mechanism.
7. Uses a separate intent classifier that misclassifies conversational follow-ups.
8. Uses different models or prompts for different conversation stages.

Fix the actual cause.

### Implementation requirements

* Maintain a proper sequence of user and assistant messages.
* Preserve the active conversation's context across turns.
* Associate each message with the correct session or conversation identifier.
* Ensure that the current user message is included exactly once.
* Avoid duplicating previous assistant messages.
* Apply context-window management without dropping essential recent turns.
* Preserve the relationship between the user's current question and the preceding assistant response.
* Prevent unrelated retrieved documents from changing the meaning of the user's follow-up.
* Ensure that conversation history is not accidentally shared between unrelated users or sessions.

If a separate contextual query-rewriting step exists, inspect its output and correct it as necessary.

For example:

Conversation:
Assistant: "You could visit Shaniwar Wada, Aga Khan Palace, and Dagadusheth Halwai Ganapati Temple."

User: "As I was planning to visit these places."

The system should understand that "these places" refers to the three landmarks.

It should not reinterpret the message as a request to visit the college.

### Expected response

"Nice! You could start with Shaniwar Wada, then visit Dagadusheth Halwai Ganapati Temple, and keep Aga Khan Palace for later. Check travel times before you leave, since traffic in Pune can be unpredictable."

The exact itinerary may vary, but the conversational reference must remain correct.

---

## 5. SEPARATE GENERAL KNOWLEDGE FROM INSTITUTIONAL KNOWLEDGE

Buddy should be capable of answering both institutional questions and general questions.

Implement a clear routing strategy using the architecture already present in the repository.

Possible request categories include:

1. Institutional questions.
2. General knowledge questions.
3. Local travel and recommendations.
4. Questions about specific people.
5. Current or time-sensitive information.
6. Follow-up questions.
7. Questions requiring document retrieval.
8. Questions requiring external search.
9. Questions that can be answered directly without retrieval.

Do not automatically force every request through the APCOER knowledge base.

### Example: General question

User:
"Who is President of China?"

Buddy should answer directly:

"Xi Jinping is the president of China."

If the model or a verified current source supports additional context, Buddy may include it.

The answer must not begin with:

"Hello there! I am BUDDY, your friendly AI receptionist here at APCOER Pune."

It must not end with an irrelevant question about college departments.

For current officeholders, the system should use a supported verification mechanism when available and appropriate. If current verification is unavailable, do not falsely claim that the answer has been checked against current records.

### Example: Institutional question

User:
"Who is the principal of APCOER?"

Buddy should search the institutional knowledge base for relevant, current information.

If the information is found in an authoritative institutional source, answer directly and cite that source through the existing citation mechanism.

If the information is not found, explain that the available institutional sources do not establish the answer.

Do not fabricate a name.

### Example: Mixed question

User:
"Which places in Pune should I visit before coming to APCOER?"

Buddy should address both parts of the question.

It should not ignore the tourist recommendations and focus exclusively on the campus.

### Important implementation detail

If the project already has an intent classifier or query router, improve it rather than adding another unnecessary layer.

Do not rely exclusively on brittle keyword matching such as detecting "college," "professor," or "Pune."

Use the current architecture's most reliable approach, which may include LLM-based routing, deterministic rules for obvious cases, or a hybrid system.

Keep the implementation efficient enough for the existing deployment environment.

---

## 6. FIX THE RETRIEVAL-AUGMENTED GENERATION PIPELINE

The response concerning Professor Akash Dorke raises a question about the quality of the institutional knowledge base and its retrieval process.

Buddy currently states that it cannot find the professor in its faculty directory.

That answer could be correct, but we need to establish whether the system genuinely searched the appropriate sources.

### Investigate the complete retrieval pipeline

Inspect:

* Document ingestion.
* Text extraction.
* PDF and other file parsing.
* Chunking strategy.
* Chunk overlap.
* Embedding generation.
* Vector database or document index.
* Metadata extraction.
* Similarity search.
* Keyword search.
* Hybrid retrieval, if supported.
* Reranking, if implemented.
* Context construction.
* Source attribution.
* Final answer generation.

Determine whether the faculty directory is present in the indexed knowledge base.

Do not assume that the knowledge base contains information merely because the application displays a source count.

### Required improvements

1. Ensure that institutional documents are actually ingested and indexed.
2. Preserve document titles, URLs or file references, dates, and relevant metadata.
3. Improve retrieval of faculty names, department names, designations, and abbreviations.
4. Support exact-name searches and reasonable spelling variations.
5. Use keyword retrieval alongside semantic retrieval where appropriate.
6. Avoid allowing loosely related documents to dominate the answer.
7. Use reranking if it is already available or can be added without unreasonable complexity.
8. Ensure that the retrieved context is relevant to the current question.
9. Distinguish an unsuccessful search from a successful search that establishes that information is unavailable.
10. Avoid claiming that a faculty directory was searched unless the retrieval operation actually happened.

For faculty-name questions, consider a dedicated metadata filter or structured faculty index if the existing architecture supports it.

Do not invent a professor's department, title, biography, qualifications, or institutional role.

### Expected behavior

User:
"Who is Professor Akash Dorke?"

If reliable information is found:

"Professor Akash Dorke is [verified role or designation] in [verified department]."

Include a source reference if the answer was derived from the institutional knowledge base.

If no reliable information is found:

"I couldn't find reliable information about Professor Akash Dorke in the available APCOER records. If you know the department, I can narrow the search."

Do not claim that the person does not exist simply because retrieval failed.

Do not list unrelated faculty members to compensate for missing information.

### Retrieval quality instrumentation

Where practical, record diagnostic information such as:

* Query category.
* Number of retrieved chunks.
* Retrieved document identifiers.
* Retrieval scores.
* Whether any relevant source passed the configured threshold.
* Whether the response used institutional documents.
* Whether the answer was generated from general model knowledge.

Respect existing logging and privacy requirements. Do not log secrets, credentials, or unnecessary personal information.

Use these diagnostics to determine whether retrieval failures originate in ingestion, search, context construction, or answer generation.

---

## 7. REMOVE REPETITIVE SOURCE-COUNT MESSAGES

The current interface displays:

"4 Verified Source References"

after every answer.

This is not useful if the number is fixed, the sources are irrelevant, or the references are not actually verified.

Investigate the source-count implementation and determine why the same count appears repeatedly.

### Required behavior

* Display sources only when meaningful source information is available.
* Show the actual sources used to support an answer.
* Do not fabricate source titles, links, document identifiers, or verification claims.
* Do not display a fixed number of sources for every response.
* Do not show irrelevant APCOER sources beneath unrelated general-knowledge answers.
* Do not count duplicate chunks from the same document as independent verified sources.
* Distinguish retrieved documents from externally verified information.
* Avoid displaying raw internal retrieval metadata to the user.
* Preserve useful source citations for institutional questions.

If the application has a source panel or expandable references section, improve that existing interface instead of creating an unnecessary replacement.

### Example

For a general question:

User:
"Who is President of China?"

Buddy:
"Xi Jinping is the president of China."

There should be no irrelevant college-source panel.

For a faculty question supported by a document:

Buddy:
"According to the available faculty directory, [verified answer]."

The interface should expose the actual relevant document reference.

If the answer is generated without retrieved sources, do not present institutional references as evidence for it.

---

## 8. MAKE THE LANGUAGE NATURAL AND CONCISE

Buddy currently sounds excessively formal and promotional.

For example:

"I would be delighted to share some wonderful spots you should explore around our vibrant city!"

This is unnecessarily verbose for a straightforward question.

### Required response style

* Friendly.
* Natural.
* Direct.
* Clear.
* Context-aware.
* Concise by default.
* Detailed when the user requests detail.
* Professional when the context requires professionalism.

Avoid:

* Repeated "Hello there!" introductions.
* Repeatedly stating "I am Buddy."
* Repeated "I would be delighted" phrases.
* Excessive exclamation marks.
* Repetitive offers to help.
* Unnecessary promotional references to APCOER.
* Generic closing questions after every answer.
* Unrequested claims about the assistant's identity or role.

### Example: Tourist recommendations

User:
"What are places we should visit in Pune?"

Expected answer:

"You could visit Shaniwar Wada, Aga Khan Palace, Dagadusheth Halwai Ganapati Temple, Sinhagad Fort, and the Raja Dinkar Kelkar Museum. If you have a full day, I can help arrange them into a practical itinerary."

The model may adjust the response to match available verified information.

The important requirement is to answer naturally without introducing the college.

### Example: Follow-up

User:
"As I was planning to visit these places."

Expected answer:

"Great! I can help you plan the route. How much time do you have—half a day or a full day?"

The answer must use the preceding context.

### Example: General knowledge

User:
"Who is President of China?"

Expected answer:

"Xi Jinping is the president of China."

Do not add an irrelevant institutional greeting or closing question.

### Avoid overcorrecting

Do not force every answer to be extremely short.

If the user asks for a detailed explanation, itinerary, technical answer, or institutional overview, provide the required detail.

Conciseness should be the default, not an arbitrary response-length limit.

---

## 9. FIX TEXT-TO-SPEECH PRONUNCIATION

Buddy appears to pronounce APCOER as:

"A, P, C, O, E, R."

Investigate whether the problem originates in:

* The generated text.
* A text-normalization layer.
* The text-to-speech model.
* SSML or phoneme configuration.
* Acronym handling.
* The voice engine's pronunciation dictionary.
* Streaming text segmentation.

### Requirements

1. Preserve the correct written form of APCOER in the chat interface.
2. Avoid unnecessarily inserting spaces or punctuation between its letters.
3. If the TTS engine supports pronunciation dictionaries, SSML, or phoneme overrides, configure an appropriate spoken form.
4. If an acronym expansion is more natural, use it only when appropriate to the context.
5. Keep text normalization separate from the original displayed answer when necessary.
6. Avoid modifying ordinary words and names indiscriminately.
7. Test both streamed and non-streamed speech if both are supported.

Do not blindly replace every occurrence of APCOER with a guessed pronunciation.

Choose the pronunciation based on the institution's intended spoken name and the actual TTS engine's capabilities.

Do not allow pronunciation fixes to alter source URLs, identifiers, or the text displayed in the conversation.

---

## 10. PRESERVE GENERAL KNOWLEDGE AND OFFLINE CAPABILITIES

Buddy should not become dependent on institutional documents to answer ordinary questions.

If the application supports a local LLM, preserve that functionality.

Investigate how the current application chooses between:

* Local model inference.
* Institutional retrieval.
* External web search.
* Cached information.
* Other available model providers.

### Required behavior

For ordinary questions that the local model can answer, allow it to respond without requiring internet access.

For institution-specific questions, use the local knowledge base when available.

For current or time-sensitive questions, use a supported current-information source when one is available and the task requires it.

If no live source is available, avoid pretending that information has been freshly verified.

Do not introduce a mandatory web dependency for all requests.

Do not remove existing offline functionality or unnecessarily increase model requirements.

If a routing mechanism already exists, improve it rather than building a second independent routing system.

---

## 11. ADD CONVERSATION AND RESPONSE QUALITY TESTS

Create automated regression tests using the project's existing testing framework.

If no testing framework exists, introduce a lightweight test setup appropriate to the current stack.

Tests should verify observable behavior rather than exact wording.

### Test A: General recommendations

User:
"What are places we should visit in Pune?"

Expected:

* Returns relevant Pune attractions.
* Does not unnecessarily introduce APCOER.
* Does not claim to be a receptionist.
* Does not append irrelevant institutional references.

### Test B: Contextual follow-up

Assistant previously recommends three Pune attractions.

User:
"As I was planning to visit these places."

Expected:

* Understands that "these places" refers to the previously recommended attractions.
* Continues the travel-planning conversation.
* Does not redirect the user toward the college.

### Test C: General knowledge

User:
"Who is President of China?"

Expected:

* Answers the actual question.
* Does not introduce APCOER unnecessarily.
* Does not claim live verification unless a verification operation occurred.

Where currentness matters, validate the answer against an appropriate test fixture or current-information provider.

### Test D: Faculty lookup

User:
"Who is Professor Akash Dorke?"

Expected:

* Attempts the appropriate institutional retrieval operation.
* Uses the available evidence.
* Does not fabricate a designation or biography.
* Acknowledges uncertainty when the records are insufficient.

Test both a successful retrieval and an unsuccessful retrieval.

### Test E: Institutional information

User:
"Who is the principal of APCOER?"

Expected:

* Searches the relevant institutional knowledge base.
* Answers from available authoritative evidence.
* Provides a useful source reference when supported.

### Test F: Follow-up about a person

Assistant provides verified information about a professor.

User:
"Which department does he belong to?"

Expected:

* Resolves "he" to the previously discussed professor.
* Uses available evidence.
* Does not search for an unrelated person.

### Test G: No unnecessary introduction

Send several unrelated questions in the same session.

Expected:

* Buddy does not begin every response with a greeting.
* Buddy does not repeatedly announce its name or role.

### Test H: Citation integrity

Ask a question that does not require institutional retrieval.

Expected:

* No fabricated institutional citations.
* No fixed "4 Verified Source References" label unless four genuinely distinct and relevant sources were actually verified and used.

### Test I: Session isolation

Create two separate sessions with different contexts.

Expected:

* Each session uses its own history.
* Neither session accidentally inherits the other's conversation.

### Test J: Text-to-speech

If automated audio testing is supported, verify the pronunciation of APCOER using the configured voice engine.

Otherwise, test the normalized text and document the manual audio-validation procedure.

### Test K: Offline operation

If local-model operation is supported, disable network-dependent services in an appropriate test environment.

Expected:

* Basic supported questions remain answerable offline.
* The system does not falsely claim to have searched external sources.
* Missing offline information is handled gracefully.

---

## 12. ADD DEBUGGING AND EVALUATION CAPABILITIES

Where practical, make it possible to determine why Buddy produces an incorrect response.

Add structured diagnostic logging for:

* Selected request category.
* Whether the request is a follow-up.
* Conversation-history length.
* Whether contextual rewriting was used.
* Retrieval status.
* Number of relevant retrieved documents.
* Selected model or inference provider.
* Whether external search was performed.
* Citation-generation status.

Do not expose internal diagnostic information to ordinary users.

Do not log sensitive information unnecessarily.

If the application has an existing debugging panel, extend it rather than adding a separate interface without need.

Consider adding a small repeatable evaluation suite that measures:

* Correct intent classification.
* Follow-up reference resolution.
* Retrieval relevance.
* Citation accuracy.
* Unsupported-claim frequency.
* Response relevance.
* Unnecessary persona mentions.

The evaluation should help prevent regressions when prompts, models, or retrieval settings change.

---

## 13. IMPLEMENTATION CONSTRAINTS

Follow these rules throughout the work.

1. Inspect the actual code before making changes.
2. Preserve the existing technology stack unless a change is justified.
3. Avoid unnecessary rewrites.
4. Preserve existing API contracts unless a change is required and coordinated.
5. Preserve current application functionality.
6. Do not remove institutional retrieval to make general answers easier.
7. Do not replace the knowledge base with hardcoded responses.
8. Do not hardcode answers for the example questions as the primary fix.
9. Do not add unnecessary LLM calls to every request.
10. Avoid introducing additional dependencies without a clear benefit.
11. Do not expose secrets, credentials, or API keys.
12. Preserve existing offline capabilities.
13. Ensure frontend and backend response schemas remain compatible.
14. Keep the implementation maintainable and appropriately documented.
15. Run relevant tests after making changes.
16. Fix regressions introduced by the implementation.
17. Do not claim that a test passed unless it was actually run.
18. Do not claim that the model's real-world accuracy has improved without appropriate evaluation evidence.

If a required capability cannot be implemented because a dependency, provider, or dataset is unavailable, document the limitation clearly rather than pretending it has been fixed.

---

## 14. REQUIRED WORKFLOW

Execute the work in this order.

### Phase 1: Inspect

* Examine the repository structure.
* Identify the LLM integration.
* Locate the system prompt.
* Trace the chat request from frontend to backend.
* Inspect conversation-history construction.
* Trace the retrieval pipeline.
* Identify the citation-generation and display components.
* Inspect TTS processing.
* Identify the existing test infrastructure.

### Phase 2: Diagnose

Write a concise internal diagnosis of the actual root causes found in the code.

Distinguish confirmed defects from hypotheses.

Do not assume that every symptom has the same root cause.

### Phase 3: Plan

Define the smallest coherent set of changes that addresses the confirmed problems.

Prioritize:

1. Correct conversational context.
2. General-purpose assistant behavior.
3. Appropriate institutional retrieval.
4. Accurate source attribution.
5. Natural response generation.
6. TTS pronunciation.
7. Regression testing.

### Phase 4: Implement

Make the changes on:

`feature/buddy-conversation-intelligence`

Update the actual system prompt, context handling, retrieval logic, source rendering, or TTS implementation as required by the diagnosis.

Do not stop after producing a plan. Implement the changes.

### Phase 5: Validate

* Run unit tests.
* Run relevant integration tests.
* Run the conversation regression tests.
* Check the frontend and backend response formats.
* Verify citation behavior.
* Check local-model compatibility where applicable.
* Test the actual application flow if the environment supports it.
* Inspect the final Git diff.

### Phase 6: Report

Provide a concise but useful implementation report containing:

1. The confirmed root causes.
2. The files changed.
3. The behavior improvements implemented.
4. The tests executed.
5. The actual test results.
6. Any unresolved issues.
7. Any dependencies or configuration changes required.
8. The feature branch name.
9. Any manual verification steps still required.

Do not commit or merge changes unless explicitly requested.

---

## 15. DEFINITION OF DONE

The task is complete only when the implementation has been updated and validated against the relevant tests.

Buddy should now behave like a natural, intelligent assistant rather than a scripted college receptionist.

The following must be true:

* It answers general questions without forcing APCOER into the conversation.
* It maintains context across follow-up messages.
* It correctly understands references such as "these places."
* It retrieves institutional information when relevant.
* It does not invent faculty details.
* It does not expose fabricated or irrelevant source references.
* It uses natural, appropriately concise language.
* It avoids unnecessary greetings and self-introductions.
* Its TTS pronunciation is improved where the current engine supports a reliable correction.
* Its offline capabilities remain intact where currently supported.
* Automated regression tests cover the principal failure cases.
* All modifications are isolated to the new feature branch.
* The implementation report accurately reflects what was and was not tested.

Begin by creating the feature branch and inspecting the repository. Then diagnose, implement, test, and report.

The goal is not to make Buddy sound different for four example questions. The goal is to fix the underlying behavior so it can handle a wide variety of natural conversations correctly.
