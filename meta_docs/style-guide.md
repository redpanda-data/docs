# Redpanda Documentation Style Guide
The Redpanda Documentation Style Guide provides guidance on writing product documentation. 

## Style guide update and approval process
This guide is intended to be helpful to documentation team writers and reviewers. 

- If you are a member of the Redpanda documentation team, you should propose your updates to your docs team peers before adding to this document. For example, you can demo at a team meeting or in the #doc-team Slack group.

- If you are not a member of the Redpanda doc team, you should start a conversation on [the community channel](https://redpanda.com/slack).

# Organization of product documentation
Before you start writing, create an outline with the information you intend to add to each section. It might look something like this:

- **Overview** - This is an introduction to the feature and contains use cases, architecture, and any important notes, such as whether the feature is in technical preview.

    - **Always include use cases** - What will the user be able to accomplish with the feature? Examples are great!

- **Configuration or Setting up** - This section contains everything Redpanda users need to do before using the feature. You can split this into multiple subheadings that contain information about configuration parameters, initial commands they need to run, etc. This can be in paragraph form or a list of steps, depending on what will provide the best possible user experience.

    - **Prerequisites** - This should be a bullet list toward the beginning of the **Setting up** section. Include all software and hardware requirements. 

- **Conceptual information** - Sections that are titled according to the requirements of the feature. Split them up into short sections of a few paragraphs. Use bullet lists and code blocks to make the text easier to read.

- **How-to information** - If step-by-step actions are required to use the feature, place them here. This can be useful for customers who are trying to complete a task quickly without wading through the conceptual information in the previous sections.

- **Reference material** - This can be anything; for example, a simple list of additional configuration parameters.

- **Troubleshooting or debugging information** - If troubleshooting or debugging information is available, place in this section.

- **What’s next** - After a customer completes the task described, what is the next logical step in their implementation journey? Include appropriate links to logical next steps that will help guide them through the adoption, implementation, and deployment process.

# Language and grammar

## Capitalization and punctuation 
__**Important:**__ These are meant as guidelines for new topics. If you are updating an existing topic, follow the existing capitalization convention in that topic. For example, if a topic is using title case, then use title case so it matches. Mixing title types is worse than not following the style guide.

- For navtree topic titles (those appearing in the primary topic navtree), use init caps. For example: “Technical Preview”, or “Consumer Offsets”.

- For h2 and lower headings (those appearing in the right navigation pane), use sentence style capitalization. For example,  “Editing cluster properties”, or “Prepare infrastructure”.

In text, follow the standard capitalization rules for American English. Additionally:

- Don't use all uppercase for emphasis.

- Follow the official capitalization for the names of brands, companies, software, products, services, and the like.

- Avoid camel case and all caps. Some screen readers read capitalized letters individually, and some languages are unicase.

- Capitalization in lists: Use sentence case for items in all types of lists.

- Do not capitalize general terms, such as worker, workers, consumer, producer, topic, cluster, etc.

- Use parentheses judiciously. Don't put important information in parentheses if you can help it. 

## Commands and code
Don’t start a sentence with a command or code. Instead, try to move the code into the middle of the sentence. Introduce the command with the more descriptive word “run” instead of “use the X command".

- **Correct:** Run the rpk topic create command to create a new topic. 

- **Incorrect:** rpk topic create creates a new topic. 

Similarly, do not start a sentence with a filename. For example: 

- **Correct:** The redpanda.yaml file contains configuration parameters. 

- **Incorrect:** redpanda.yaml contains configuration parameters. 

## Commas
Use serial (Oxford) commas. In a series of three or more items, use a comma before the last item (before the and or or). 

- **Correct:** The purchase event is defined by product, payment, and delivery.

- **Incorrect:** The purchase event is defined by product, payment and delivery.

## Contractions
We write our documentation in an informal tone, so you can use most types of contractions.

**Negation contractions**

In particular, it's fine to use -n't contractions, such as isn't, don't, and can't.

One reason that such contractions are useful is that it's sometimes easy for a reader to miss the word not, whereas it's harder to misread don't as do.

**Noun + verb contractions**

In general, avoid contractions formed from nouns and verbs.

**Recommended:** The browser is fast, simple, and secure.

**Not recommended:** The browser's fast, simple, and secure.

The first example is better because using 's in place of is could cause the reader to think that browser's is the possessive form.

In some cases, it's okay to use a noun + verb contraction, such as, "If you want to display information, a table's your best option." However, in general, try to avoid that kind of contraction.

**Recommended:** The following guides are a good way to learn to use Universal Analytics.

**Not recommended:** The following guides're a good way to learn to use Universal Analytics.

**Don't use double contractions**

Double contractions contain not just one but two contracted words. Some examples of double contractions are as follows:

- mightn't've (mightn't have → might not have)

- mustn't've (mustn't have → must not have)

- wouldn't've (wouldn't have → would not have)

- shouldn't've (shouldn't have → should not have)

**Its and It’s**

Don't confuse its (possessive) with it's (noun + verb).

## Filenames
Make file and directory names lowercase. In general, separate words with hyphens, not underscores. Use only standard ASCII alphanumeric characters in file and directory names.

## Titles and headings
In the titles and headings that show up in the left nav, use [title case](https://en.wikipedia.org/wiki/Title_case) (for example, “Node Management”).

In section titles within a doc, `<h2>` and below, use [sentence case](https://en.wikipedia.org/wiki/Letter_case#Sentence_case) (for example, “Available versions”).

Always use the imperative in headings. For example, use “Configure Producers” instead of “Configuring Producers”.

# Voice and tone
- Use the second person ("you") when speaking to or about the reader.
- Don’t use "we", "our", or "let's" as if author and reader were a hybrid entity.
**Good:** "Configure your terminal window"
**Bad:** "We configure the terminal window" or "The terminal window is configured"

- Start task instructions with the imperative. For example, say “Set the environment variable” instead of “To set the environment variable” or “You can set the environment variable”.

- Focus on facts, real user tasks, and real user benefits. Avoid promotional hype at all
costs.

- Use shorter words over longer alternatives. Examples: "helps" rather than "facilitates"
and "uses" rather than "utilizes."

- Use active voice where possible. Passive voice is acceptable when any of these
conditions is true:
  - The system performs the action.
  - It is more appropriate to focus on the receiver of the action.
  - You want to avoid blaming the user for an error, such as in an error message.
  - The information is clearer in passive voice.

* Avoid calling out the version in text ("Starting in version x.x...") unless the feature was slipped in during a point/patch release and not announced in major version Release Notes. 

* Avoid using future tense, such as "will". Especially avoid the use of future and
passive used in tandem, such as "will not be". 

* If a sentence contains a conditional phrase, put it at the beginning of the sentence. That way, the reader can skip the rest of the sentence with confidence if the condition doesn't apply.

* Aim for economical expression. Omit weak modifiers such as "quite," "very," and
"extremely." Weak modifiers have a diluting effect.

* Avoid weak verbs such as "is," "are," "has," "have," "do," "does," "provide," and "support." Weak verbs require more wordy constructions. Don’t start a sentence with "There is..." or "There are...", which are empty phrases that add no meaning. Instead, rearrange the sentence so the subject comes first. For example, change “There are three ways to do this” to “You can do this in three ways”.

# GUI style guidelines
## Screenshots
- Avoid including screenshots in product documentation. If you must include a screenshot, do so sparingly and strategically. Focus images on the specific UI feature (in other words, don't capture the left nav unless necessary).

- Screenshots create technical debt, since they must be maintained as the product changes. They also create a localization burden.

## Referring to UI elements
Because UI design changes occur often and without notice (no doc Issue filed), avoid referring to the exact location of an interface control if possible.

**Navigation menu**

Refer to the leftmost navigation menu as "navigation menu" rather than the general term "interface." You can direct users to submenu items with the bracket symbol (>). For example, "From the navigation menu, select Deployment > Starting a local cluster."

**Pages**

When users select an item from the navigation menu, they land on a page. For example, a user would select Security from the navigation menu, and the Security page displays.

**Panes**

Areas within a dialog or page are referred to as a “pane.” 

**Minimalism**

To write in a minimalist style, omit words like "the" and "button." It cuts down on potential translation costs and prevents maintenance if the UI design changes. For example, instead of writing, “Click the **Add** button,” write “Click **Add**.”

# Abbreviations for units of measure
| Unit of Time or Measurement | Abbreviation |
|-----------------------------|--------------|
| byte                        | B            |
| bit                         | b            |
| bits per second             | bps          |
| gigabyte                    | GB           |
| gigabit                     | Gb           |
| gigabytes per second        | GBps         |
| gigabits per second         | Gbps         |
| kilobyte                    | KB           |
| kilobit                     | Kb           |
| kilobytes per second        | KBps         |
| megabyte                    | MB           |
| megabit                     | Mb           |
| megabytes per second        | MBps         |
| megabits per second         | Mbps         |
| milliseconds                | ms or msec   |

# Acronyms or abbreviation
In general, when an abbreviation is likely to be unfamiliar to the audience, spell out the first mention of the term and immediately follow with the abbreviation in parentheses.

# Cross-references
Cross-reference links should be constructed to provide meaning ("why") before the link. Introduce links to other documentation topics with “see”, not “refer to”. Be mindful that users on mobile might have a hard time clicking on small links. 

- Use meaningful [link text](https://developers.google.com/style/link-text).
    **Correct:** To begin coding right away, see [Building your first app](https://developer.android.com/training/basics/firstapp).
    **Incorrect:** Click [here](https://docs.redpanda.com/docs/security/).
    **Incorrect:** See [this blog post](https://redpanda.com/blog/solve-out-of-memory-killer-events).

- If a link downloads a file, then make that clear in the link text, and mention the file type.
    **Correct:** For more information, see [download the security features PDF](https://www.example.com/security.pdf).

- If the link text doesn’t clearly indicate why you're referring the reader to this information, then give an explanation. Make the explanation specific, but don't repeat the link text.
    **Correct:** For more information about authentication and authorization, see [Using OAuth 2.0 to access Google APIs](https://developers.google.com/identity/protocols/oauth2).

- Do not link to outside sources like wikipedia for definitions. Every link can distract readers away from the reason they came to that page in the first place.

# Example domains and names
- Do not use abbreviations that are profane (RTFM, IDGAF). 

- Do not use examples that contain any customer-identifiable information, such as CLASSPATH.

# File types
When you're discussing a file type, use the formal name of the type. (The file type name is often in all caps because many file type names are acronyms or initialisms.) Do not use the filename extension to refer generically to the file type.

The following table lists examples of filename extensions and the corresponding file type names to use.

| Extension   | File type name  |
|-------------|-----------------|
| .csv        | CSV file        |
| .exe        | executable file |
| .gif        | GIF file        |
| .img        | disk image file |
| .jar        | JAR file        |
| .jpg, .jpeg | JPEG file       |
| .json       | JSON file       |
| .pdf        | PDF file        |
| .png        | PNG file        |
| .proto      | Proto file      |
| .ps         | PowerShell file |
| .py         | Python file     |
| .sh         | Bash file       |
| .sql        | SQL file        |
| .svg        | SVG file        |
| .tar        | tar file        |
| .txt        | text file       |
| .yaml       | YAML file       |

# Fonts and variables
Specific fonts for specific types of text.

## Code fences 
We use monospace fonts in the same contexts across teams. The following types of text should be denoted as code: 

| Text                              | Example                              |
|-----------------------------------|--------------------------------------|
| CLI commands                      | rpk topic create                     |
| File paths                        | /lib/systemd/system/redpanda.service |
| File types                        | .yaml, .log                          |
| Filenames                         | redpanda.yaml                        |
| rpk                               | rpk                                  |
| Tags and configuration parameters | rp-type=topic-manifest               |


## Code blocks
Use code blocks for large blocks of code, file snippets, or commands that you want to make easy to read and copy. 

## Bold text
Use bold text to indicate that a string is UI text. Do not use a bold font to emphasize a word or phrase. 

   - **Correct:** Enter a name for the new cluster in the Cluster name field.

   - **Incorrect:** You must have Redpanda version 21.11.3 or later installed to use Shadow Indexing.

## Quotation marks
Do not use quotation marks. Check the sections in this guide for italics and bold, and if those situations do not apply, reword your sentence to alleviate the need for the quotation marks.

# Future features or releases
Avoid mentioning any future features or releases within the documentation. Such referrals could be construed as a promise to deliver, which is not within the scope of product documentation.

# Placeholders
Placeholders in sample code and commands represent values that the user must replace. Placeholders in example output can also represent other values that vary. A placeholder has a descriptive name as its value. Separate words with a dash. **Do not** use possessives or instructions as values, such as replace-with or my-value.

If your sample code and command placeholders occur in a sentence, use the following formatting:

`<placeholder-value>`

When you use a placeholder in text or code, explain the placeholder the first time you use it. It's not necessary to repeat the explanation in the document unless doing so might benefit the user. For example:

    Create the topic.

    ```
    rpk topic create <topic-name>
    ```

    Replace <topic-name> with your own topic name.

# Images
When possible, use images to supplement the documentation text. You might want to use any of the following types of images:

- Architecture diagrams

- UI screenshots

- Charts and graphs

# Linking
If the server that you're linking to supports HTTPS, start the URL with https. If the server doesn't support HTTPS, start the URL with http.

# Metadata
To improve the SEO rankings of Redpanda product documentation, include the following metadata tags at the top of all content files:

```
<head>

    <meta name="title" content="Additional configuration | Redpanda Docs"/>

    <meta name="description" content="Additional configuration parameters for the Redpanda operator."/>

</head>
```

## Notes and warnings
Redpanda product documentation uses admonitions to bring awareness to a topic. 

| Notice  | Description                                                                                                                                                                                                                                           |
|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Note    | A supplement to the documentation with helpful information.                                                                                                                                                                                           |
| Tip     | Describes a way to make things easier or indicates a best practice.                                                                                                                                                                                   |
| Info    | Additional information for the reader’s benefit if they want to dive deeper, but is not necessary to understand for the current documentation.                                                                                                        |
| Caution | A warning that certain behavior is unexpected or may have unintended consequences. Also use this to indicate that a feature is in technical preview. See the Technical previews section of this wiki for more information about tech preview notices. |
| Danger/Warning  | Do not use this admonition in Redpanda documentation.                                                                                                                                                                                                 |

# Numbers
For whole numbers between one and nine, spell out the number (for example, nine instead of 9). For numbers greater than 9, or any decimal or negative number, use Arabic numerals (for example, 1.5 or -2). 

  - **Correct:** To run Redpanda in a three-node cluster, use this command: rpk container start -n 3

  - **Incorrect:** To run Redpanda in a 3-node cluster, use this command: rpk container start -n 3

The exception to this is within code or when you’re referring to a default value. For example: 

  - **Correct:** cloud_storage_upload_ctrl_d_coeff - The derivative coefficient for the upload controller. Default is 0.

  - **Incorrect:** cloud_storage_upload_ctrl_d_coeff - The derivative coefficient for the upload controller. Default is zero.

# Personally identifiable information
- Do not include links to personal blogs or non-Redpanda assets. 

- Do not use any examples that contain any customer or Redpanda-internal identifiable information (for example, CLASSPATH info from a customer).

# Property descriptions
If you have just a few properties to describe, you can define them in a bulleted list. Put the property name in code font, followed by a dash and the description. The description does not have to be a complete sentence. After the description, add the default value by writing __Default: <value>__. For example:

- `property_name` - Property description. Default: value

Here’s an example as it would appear in the documentation:

- `cloud_storage_upload_ctrl_p_coeff` - The proportional coefficient for the upload controller. Default: -2

If you have three or more properties, you can put them in a table. The table should have two columns: Property and Description. The Property column only includes the property name. The Description column includes a description of the property, which does not have to be a complete sentence, followed by the default value: __Default: <value>__.

Here’s an example of a table:

| Property                                     | Description                                                                                  |
|----------------------------------------------|----------------------------------------------------------------------------------------------|
| <code>cloud_storage_upload_ctrl_update_interval_ms</code> | Recompute interval for the upload controller. Default: 60000 ms.                             |
| <code>cloud_storage_upload_ctrl_p_coeff</code>            | Proportional coefficient for the upload controller. Default: -2                              |
| <code>cloud_storage_upload_ctrl_min_shares</code>         | The minimum number of I/O and CPU shares that the remote write process can use. Default: 100 |

For adding or editing properties on a page with many properties, such as a reference page of properties, define each property within a heading.

# Tables
Tables can be helpful for visualizing information or as a reference after reading the documentation. The Tiered Storage topic contains tables that are a different way of presenting the same information that’s included in the text. 

# Technical previews
When a feature is in technical preview you must identify it as such in two places: 

- The technical preview page under the Introduction heading.

- In a **Caution** box on the feature page. 

# Word list

| Term                          | Description                                                                                                                                                                                                                                                                                                                                                                                                 | Examples                                                                                                                                                                                                                                                                                                                                |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| (s)                           | Do not use to indicate an optional plural. Use the plural.                                                                                                                                                                                                                                                                                                                                                  |                                                                                                                                                                                                                                                                                                                                         |
| Access control list (ACL)     | Spell it out the first time you introduce it on a page, with the acronym in parentheses. After that, you can just use the acronym. Always capitalize the acronym. Do not capitalize access control list unless it’s the first word in a sentence. The plural is ACLs. First time you introduce it on a page: access control list (ACL), access control lists (ACLs). All subsequent references on the page. |                                                                                                                                                                                                                                                                                                                                         |
| as well as                    | Do not use to mean "and."                                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                         |
| backend                       | Do not use "back end."                                                                                                                                                                                                                                                                                                                                                                                      |                                                                                                                                                                                                                                                                                                                                         |
| broker                        | A Redpanda broker acts as a server that processes write requests from producers, and read requests from consumers. A Redpanda broker acts as a server that processes write requests from producers, and read requests from consumers. A Redpanda broker is a process that runs on a node (a machine or a VM) in a Redpanda cluster. A Redpanda broker is sometimes referred to as a Redpanda node.          | rpk commands use the term broker. For example, rpk redpanda admin brokers [command]                                                                                                                                                                                                                                                     |
| built-in                      | Write as a hyphenated combination.                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| certificate authority         | Spell out the first time you introduce it on a page, with the acronym in parentheses. After that, use the acronym. Always capitalize the acronym. Do not capitalize "certificate authority” unless it’s the first word in a sentence. The plural is “CAs”.                                                                                                                                                  | First appearance on a page: certificate authority (CA), certificate authorities (CAs) <br/><br/>All subsequent references on the page: CA, CAs <br/><br/>Incorrect: ca, cas, Certificate Authority                                                                                                                                                          |
| check out                     | Write as two words when using as a verb form.                                                                                                                                                                                                                                                                                                                                                               | For example: Check out the x.y.z branch. Note that “checkout” is a noun.                                                                                                                                                                                                                                                                |
| cluster                       | Use to refer to a set of Redpanda nodes working together.                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                         |
| cross-datacenter              | Write as one word.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| Ctrl+C                        | Write Ctrl+C for the "break" key combination. Prefer Ctrl+C to other variants (like Ctrl-C, CTRL-C, CTRL+C, or ^C). The style is plain para; don't make it an inline literal.                                                                                                                                                                                                                               |                                                                                                                                                                                                                                                                                                                                         |
| datacenter                    | Write as one word.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| datastore                     | Write as one word.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| Debian                        | Write as Debian, not DEB.                                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                         |
| direct memory access          | Spell it out the first time it appears on a page, with the acronym in parentheses. After that, use the acronym. Always capitalize the acronym. Do not capitalize unless it’s the first word in a sentence.                                                                                                                                                                                                  | First appearance on a page: direct memory access (DMA) <br/><br/>All subsequent references on the page: DMA <br/><br/>Incorrect: dma, Direct Memory Access                                                                                                                                                                                                  |
| disaster recovery             | Write as two words (do not abbreviate or use the acronym “DR”).                                                                                                                                                                                                                                                                                                                                             |                                                                                                                                                                                                                                                                                                                                         |
| endpoint                      | Write as one word.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| event streaming               | TO DO: Check out PM word list to ensure we use event streaming/data streaming correctly and consistently.                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                         |
| event                         | TO DO: Clarify difference (if there is one) between usage of “event” vs “message”. Check with PM to see which term RP docs should use and update here.                                                                                                                                                                                                                                                      |                                                                                                                                                                                                                                                                                                                                         |
| filename                      | Write as one word.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| fintech                       | Lowercase unless at the beginning of a sentence.                                                                                                                                                                                                                                                                                                                                                            | Correct: fintech <br/><br/>Incorrect: Fintech, FinTech                                                                                                                                                                                                                                                                                            |
| for example                   | Do not use "e.g." Use “for example”, “such as”, or “like” as appropriate.                                                                                                                                                                                                                                                                    |                                                                                                                                                                                                                                                                                                                                         |
| frontend                      | Write as one word. Do not use "front end."                                                                                                                                                                                                                                                                                                                                                                  |                                                                                                                                                                                                                                                                                                                                         |
| Google Cloud Platform         | Spell out the first time it appears on a page, with the acronym in parentheses. After that, use the acronym.                                                                                                                                                                                                                                                                                                | First appearance on a page: Google Cloud Platform (GCP) <br/><br/>All subsequent references on the page: GCP <br/><br/>Incorrect: Google cloud platform, gcp                                                                                                                                                                                                |
| ID                            | Write as one uppercase word.                                                                                                                                                                                                                                                                                                                                                                                | <br/><br/>Incorrect: Id, id                                                                                                                                                                                                                                                                                                                       |
| input/output                  | Spell out or use the abbreviation, but always include the / character in between the terms.                                                                                                                                                                                                                                                                                                                 | Correct: input/output, I/O <br/><br/>Incorrect: Input/Output, IO, io                                                                                                                                                                                                                                                                              |
| internet                      | Do not capitalize.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| JAR file                      | Write as one uppercase word. For generic references, use uppercase and a noun.                                                                                                                                                                                                                                                                                                                              |                                                                                                                                                                                                                                                                                                                                         |
| Kafka                         | Never prepend a feature or product name with "Redpanda Kafka", because this violates ASF rules.                                                                                                                                                                                                                                                                                                             |                                                                                                                                                                                                                                                                                                                                         |
| keystore                      | Write as one word. Capitalization might depend on context. Match the parameter.                                                                                                                                                                                                                                                                                                                             | as one word. Capitalization might depend on context. Match the parameter.                                                                                                                                                                                                                                                               |
| lowercase                     | Write as one word.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| message                       | TO DO: See “event” above. After getting guidance from PM, update to clarify which term we should be using in RP docs.                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                         |
| multi-datacenter              | Write as two hyphenated words.                                                                                                                                                                                                                                                                                                                                                                              |                                                                                                                                                                                                                                                                                                                                         |
| multicloud                    | Write as a non-hyphenated word.                                                                                                                                                                                                                                                                                                                                                                             |                                                                                                                                                                                                                                                                                                                                         |
| node                          | Use to refer to an instance of Redpanda running on a machine. Refer to as “Redpanda node” or “node”, depending on context.                                                                                                                                                                                                                                                                                  |                                                                                                                                                                                                                                                                                                                                         |
| on-premises                   | Do not use "on-premise" or "on-prem".                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                         |
| operating system              | Use either “operating system” or “OS”. Do not capitalize unless it’s the first word in a sentence.                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| please                        | Do not use.                                                                                                                                                                                                                                                                                                                                                |                                                                                                                                                                                                                                                                                                                                         |
| property                      | Use to refer to settings in a configuration file.                                                                                                                                                                                                                                                                                                                                                           | Correct: To enable Shadow Indexing on a cluster, set the following properties in the redpanda.yaml file. <br/><br/>Incorrect: To enable Shadow Indexing on a cluster, set the following parameters in the redpanda.yaml file.                                                                                                                     |
| quick start                   | Write as two words.                                                                                                                                                                                                                                                                                                                                                                                         |                                                                                                                                                                                                                                                                                                                                         |
| RBAC                          | Role-Based Access Control                                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                         |
| real-time                     | Hyphenate when used as an adjective, for example, "real-time system"; two words when used as a noun, for example, "merge streams in real time"                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                                                                                                                         |
| recommend                     | Use “Redpanda Data recommends”. Do not use “we recommend”.                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                         |
| runtime                       | Not “run time” or “run-time”.                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                         |
| RPM                           | Write as RPM, not rpm.                                                                                                                                                                                                                                                                                                                                                                                      |                                                                                                                                                                                                                                                                                                                                         |
| Schema Registry               | Write as “Schema Registry”, not as “the Schema Registry”.                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                         |
| SerDes                        | Used mixed case.                                                                                                                                                                                                                                                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                                         |
| Single Message Transformation | Write using title case (as shown).                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| streaming data                | Write as two words.                                                                                                                                                                                                                                                                                                                                                                                         |                                                                                                                                                                                                                                                                                                                                         |
| that is                       | Do not use "i.e."                                                                                                                                                                                                                                                                                                                      |                                                                                                                                                                                                                                                                                                                                         |
| timestamp                     | Write this as one word.                                                                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                                                                                                                         |
| topic                         | A topic is a stream of related events. A doc topic is content in Redpanda product doc library.                                                                                                                                                                                                                                                                                                              |                                                                                                                                                                                                                                                                                                                                         |
| truststore                    | Write as one word. Capitalization might depend on context. Match when it is in a parameter.                                                                                                                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                                                                                                         |
| uppercase                     | Write as one word.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| version number                | When referring to a specific version of a product, write out the product name with the version (for example, Redpanda 21.11). When referring to the minimum version of a product required for a task, use the phrasing: Product version X.Y.Z or later.                                                                                                                                                     | Correct: Shadow Indexing is available for Redpanda 21.11.3 and later. <br/><br/>Correct: You must have Redpanda version 21.11.3 or later installed to use Shadow Indexing. <br/><br/>Incorrect: Shadow Indexing is available for Redpanda 21.11.3 and higher. <br/><br/>Incorrect: You must have Redpanda version 21.11.3 or higher installed to use Shadow Indexing. |
| via                           | Do not use.                                                                                                                                                                                                                                                                                                                                                                                                 |                                                                                                                                                                                                                                                                                                                                         |
| we                            | In general, don't use. Focus on the customer, and avoid making Redpanda the subject.                                                                                                                                                                                                                                                                                                                        |                                                                                                                                                                                                                                                                                                                                         |
| WebAssembly                   | Spell out the first time it appears on a page, with the acronym in parentheses. After that, use the acronym.                                                                                                                                                                                                                                                                                                | First appearance on a page: WebAssembly (Wasm) <br/><br/>All subsequent references on the page: Wasm <br/><br/>Incorrect: WASM                                                                                                                                                                                                                              |
| workflow                      | Write as one word.                                                                                                                                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                                                                                                                         |
| YAML                          | Write as one word, all capital letters.                                                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                                                                                                                         |

## Redpanda-specific word list

| Term                 | Description                                                                                                                                                                                                                                                                                                                                                                  | Examples                                                                                                                                                                                                 |
|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Bring Your Own Cloud | Redpanda product. Spell out the first time you introduce it on a page, with the acronym in parentheses. After that, you can use the acronym. When you spell it out, capitalize the first letter of each word. Always capitalize the acronym.                                                                                                                                 | First appearance on a page: Bring Your Own Cloud (BYOC) <br/><br/>All subsequent references on the page: BYOC <br/><br/>Incorrect: bring your own cloud, byoc, Bring your Own Cloud, BYOC (Bring Your Own Cloud)             |
| cluster resource     | For Kubernetes, Redpanda documentation refers to the cluster custom resource as the cluster resource. Sample definition: “The Redpanda operator for Kubernetes creates clusters based on the cluster custom resource. This document refers to the cluster custom resource as the cluster resource. After you install the Redpanda operator, you apply the cluster resource.” | Correct: cluster resource <br/><br/>Incorrect: custom resource                                                                                                                                                     |
| Fully Managed Cloud  | Redpanda product. Spell it out the first time you introduce it on a page, with the acronym in parentheses. After that, you can use the acronym. When you spell it out, capitalize the first letter of each word. Always capitalize the acronym.                                                                                                                              | First appearance on a page: Fully Managed Cloud (FMC) <br/><br/>All subsequent references on the page: FMC <br/><br/>Incorrect: fully managed cloud, fmc, Fully managed cloud, FMC (Fully Managed Cloud)                     |
| Pandaproxy           | Provides access to Redpanda using the RESTful API. Now referred to as HTTP Proxy. If <code>pandaproxy</code> is within code or a parameter, leave as-is. Otherwise, do not use this term.                                                                                                                                                                                                 | Correct: HTTP Proxy, <code>pandaproxy</code> <br/><br/>Incorrect: <code>pandaproxy</code>                                                                                                                                                    |
| Redpanda             | Name of our product. You can also use to refer to the company when there is no confusion about whether you’re referring to the company or the product. Always capitalize the first letter, do not make it into two words, and do not capitalize the p.                                                                                                                       | Correct: Redpanda <br/><br/>Incorrect: RedPanda, redpanda, Red panda                                                                                                                                               |
| Redpanda Data        | Name of the company. Use in formal settings or to distinguish between the company and the product in places where there may be confusion.                                                                                                                                                                                                                                    | Redpanda ships with a systemd service that executes periodically and reports usage and configuration data to Redpanda Data's metrics API. <br/><br/>Correct: Redpanda Data <br/><br/>Incorrect: Redpanda data, redpanda data |
| redpanda.yaml        | Redpanda’s configuration file. Refer to this as the filename, rather than configuration file or using another indirect term. Always use lowercase letters and monospace font.                                                                                                                                                                                                | Correct: <code>redpanda.yaml</code> <br/><br/>Incorrect: redpanda.yaml, Redpanda.yaml                                                                                                                                           |
| `rpk`                  | Redpanda’s CLI tool, Redpanda Keeper. Refer to as `rpk`, not Redpanda Keeper. Always use lowercase letters and monospace font. Even if it is the first word in a sentence (try to avoid), use lowercase letters.                                                                                                                                                               | Correct: <code>rpk</code> <br/><br/>Incorrect: Rpk, RPK, rpk                                                                                                                                                                    |
| Shadow Indexing      | Redpanda feature. Always spell out both words and capitalize the first letter of each word.                                                                                                                                                                                                                                                                                  | Correct: Shadow Indexing <br/><br/>Incorrect: Shadow indexing, shadow indexing, SI                                                                                                                                 |
| source-available     | Redpanda licensing model (Read more here).                                                                                                                                                                                                                                                                                                                                   | Correct: source-available code <br/><br/>Incorrect: open-source code                                                                                                                                               |

## 3rd-party brand word list
This section describes how to refer to other brands when writing about them in Redpanda product documentation.

| Term                | Examples                                                                                                                                                                                         |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Amazon S3           | First appearance on a page: Amazon S3 <br/><br/>All subsequent references on the page: S3 <br/><br/>Incorrect: Amazon AWS S3e |
| Amazon Web Services | First appearance on a page: Amazon Web Services (AWS) <br/><br/>All subsequent references on the page: AWS <br/><br/>Incorrect: aws, AWS (Amazon Web Services), Amazon web services              |
| Apache projects     | First appearance on a page: Apache Kafka® <br/><br/>All subsequent references on the page: Kafka <br/><br/>Incorrect: Apache kafka, kafka                                                        |
| Docker              | First appearance on a page: Docker <br/><br/>All subsequent references on the page: Docker <br/><br/>Incorrect: docker                                                                           |
| Grafana             | First appearance on a page: Grafana® <br/><br/>All subsequent references on the page: Grafana <br/><br/>Incorrect: grafana                                                                       |
| Zookeeper           | First appearance on a page: Zookeeper® <br/><br/>All subsequent references on the page: Zookeeper <br/><br/>Incorrect: zookeeper, zoo keeper                                                     |


## Do-not-use word list
These terms are not ideal for technical documentation, and are prohibited because they can cause confusion. 

| Term                                   | Description                                                                                                          |
|----------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| and/or                                 | Usually one of the choices fits better. Use "and" or "or." If necessary, explain as "A or B or both."
| anything pertaining to future releases | Do not refer to future releases or planned functionality. Document the product the way it is at the time of writing. |
| config                                 | configuration                                                                                                        |
| etc.                                   | Don’t use this. It can cause confusion because it’s not clear what it implies. Give concrete examples instead.       |
| e.g.                                   | Instead of this abbreviation, write out for example.                                                                 |
| foo                                    | Use a variable with contextual information instead. For example, instead of "foo", use a name that's meaningful or descriptive. Ensure that the name is applicable to the user's environment. When necessary, use an appended numbering scheme. For example, _Development_, _Staging_, _Android Development-1_, _Production-1_, or _Production-2_.  |
| for instance                           | for example                                                                                                          |
| master                                 | primary, main, original, parent, publisher, leader, active, etc.                                                     |
| once                                   | "Once" can mean one time, or it can mean "as soon as." To avoid confusion, use "after."
| please                                 | Do not use this term. In some languages and cultures, it suggests that the task or directive is optional.                 |
| should                                 | will, must                                                                    |
| slave                                  | secondary, worker, follower, etc.                                                                                    |
