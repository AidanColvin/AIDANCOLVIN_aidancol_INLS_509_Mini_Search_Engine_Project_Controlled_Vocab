Instructions:

**INLS 509-001 Information Retrieval**
**Mini Search Engine Project, Part II:**
**Mini Controlled Vocabulary**

* Please include your name and ONYEN as the first line of your submission.
* General discussion is encouraged, but everyone should come up with the solution independently.
* If you received help from anyone, give them credits by listing their name(s) on the top of your submission.
* For each answer, indicate if you used AI for help. If yes, describe how it was used in reasonable detail.

In Mini Search Engine Project Part 1: Document Collection Foraging, you started to ideate about the domain or scope of your document collection and its potential users. In particular, you have thoughts on what counts as a document in your collection, and what kinds of questions your collection can answer. Review your answer in Part 1, and keep them in mind when you work on this part. If you decide to revise or tweak your original answer in Part 1, you can give your new answer at the beginning of your submission here.

The goal of this part: Design a small set of terms that will help people search, browse, and understand your planned document collection. Your vocabulary would reflect what your users want to find and the distinctions that matter to them.

## Controlled Vocabulary: A Recap

**What is a controlled vocabulary?**
A controlled vocabulary is a set of terms/labels/tags/concepts with clear definitions. They are consistently used by both creators and users of an information retrieval system to describe, organize, and find information.

For example, a recipe collection may use the term "Quick" to mean recipes taking 30 minutes or less to prepare. Although the same concept can be named "Fast" or "Speedy," we can choose "Quick" as the preferred name for this concept to control linguistic variability. The definition makes the term more consistent than an informal impression of what counts as quick.

**Why use a controlled vocabulary in an information retrieval system?**
* **Search:** A term can retrieve relevant documents even when their wording differs. A recipe may qualify as "Mediterranean" without using that word in its title. Clear definitions can also distinguish a document about a topic from one that only mentions it.
* **Refine results:** Users can select terms to narrow a result set. For example, recipes that are both "Mediterranean" and "Quick." These interactive interface features are often known as "facets" or "filters" that appear on the side or top of a result set.
* **Browse and get an overview:** A list or hierarchy can show users what kinds of content are available and how topics connect. Users can explore and browse the topics broadly without having to search for something.

Note that these benefits rely on the system consistently tagging its documents using these terms. Also note that keyword search and controlled vocabulary search are not mutually exclusive but often complementary.

## Examples of controlled vocabularies
Below are a few examples for ideas.

* **IMDB movie genres:** A set of labels such as Comedy, Horror, and Sci-Fi, with guidance on their meanings. A movie can have multiple genres. Genres are useful since a plot summary may not mention the genre.
* **Wikipedia categories:** Categories connect articles and subcategories for browsing. One can get a bird's eye view of what a category covers by viewing its subcategories.
* **Medical Subject Headings (MeSH):** A controlled, hierarchical vocabulary from the National Library of Medicine for indexing and searching biomedical literature. It illustrates expert-curated term definitions and organization at a larger scale than this assignment requires.
* **Google Content Categories:** The category labels used by Google's Natural Language content classifier are organized into topic paths. They might also reveal how Google labels documents and queries internally to improve its results ranking.

You are not expected to replicate the scale or complexity of the above examples. You are expected to design a mini controlled vocabulary inspired by these examples.

## Your Tasks
Your submission should contain four parts as outlined below. The main questions are underlined.

### 1. Terms and definitions [50 points]
Provide a list or table of terms in your mini controlled vocabulary. Five to ten terms is a reasonable size, although it is not forbidden to have more terms. Consider to give your vocabulary a name, such as "Recipe Categories."

Each term should have:
* A unique identifier (ID), such as T01 or C002;
* A preferred name;
* A short definition or description of the term. What does the term mean? For this term to be assigned to a document, what content should the document contain, or what condition should the document satisfy? When a term could be ambiguous, it is useful to clarify boundary or exclusions: what kind of documents would not be tagged with this term?
* A list of alternative names or synonyms.

For example, a term in Recipe Categories could be:
* ID: RC04
* Preferred name: Quick
* The recipe's total preparation and cooking time is 30 minutes or less. Total time includes waiting time. If total time is unavailable, do not assign the term. So an absence of the term "Quick" does not necessarily mean the recipe takes more than 30 minutes.
* Alternative names: Fast, Speedy.

### 2. Organize your vocabulary [10 points]

**1) Structure of your vocabulary**
If no relationships exist between your terms, we say the vocabulary is a "flat list" as they are not organized in a hierarchy or a network. In that case, each term usually represent a separate topic or aspect, and we do not consider relationships between the terms. <u>Is your vocabulary a flat list or does it have relationships?</u>

If relationships are used, show them as an indented list or a labeled diagram. Define the meaning of each relationship, such as "is a type of," "is a part of," "is an aspect of," and so on. For example, if in "Recipe Categories" we have a term "Instant" to refer to cooking time less than 10 minutes, then we can say that an "Instant" recipe is a type of "Quick" recipe. An indented list may look like:
* RC04: Quick
  * RC07: Instant (a type of Quick)

**2) Term assignment considerations**
<u>Can a document in your collection be assigned one term only, or multiple terms at the same time? In other words, are your terms mutually exclusive?</u>

If your vocabulary uses a hierarchy, and a document receives a narrower term (e.g., "Instant" recipe) will it automatically receive a broader term (e.g., "Quick" recipe)? Put it another way, <u>if one searches for the broader term, should a document with a narrower term be returned</u> (e.g., if one searches for "Quick" recipes, should an "Instant" recipe be returned?) Note that this is a design choice and there is no correct answer. Either way, it will become a rule when you assign terms to your documents and subsequently affect the behavior of your search engine.

### 3. Example usage of your vocabulary [20 points]
Describe two scenarios in which you would use your controlled vocabulary when searching or refining results. One scenario uses a single term, and the other uses a combination of two terms. For each scenario, describe:
* The question in natural language. It consists of complete sentences that are more elaborate than just terms.
* The selected single term or two terms. For two terms, explicitly say whether you mean AND (return documents that simultaneously have Term A and term B) or OR (return documents that have either Term A, or Term B, or both).
* The kind of documents that are expected be retrieved or displayed.

### 4. Peer exchange [20 points]
Invite a peer classmate as a hypothetical user of your search engine.

Describe your planned document collection to them: What documents will be in the collection? Why do you think they are interesting? Also, describe your controlled vocabulary to them: What does each term mean? In what scenarios can they be useful?

Ask the user to come up with a scenario in which they would use your controlled vocabulary when searching or refining results. Ask them to explain their question in complete sentences, and take note of the term(s) they selected.

Answer the following questions:
* <u>What is the name and PID of your user?</u>
* <u>Who invited you as a user to use their search engines (if any)? What are their names and PIDs?</u>
* <u>What was your user's question in natural language?</u>
* <u>What terms did they select to represent that question?</u>
