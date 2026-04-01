---
layout: post
title: "Agentic Data"
author: "bhakyuz"
tags: ["ai", "data"]
---


Yesterday I attended to very interesting round table around AI/data organized by Nao Lab. They simple call it `agentic data` a chat bot to talk to your data. Pretty much chatGPT like interface aiming/solving multiple things at a time:
- More democratic access to data (anyone can talk to it without SQL knowledge or existing BI dashboards)
- Less need of BI tool (imagine a company where there is not BI, no Tableau, the dream comes true 😍)
- Less time spent on small/less-valuable tasks/questions for data team >> More time on value-added tasks. 

### Some facts
- With a Claud agent it cost about 50 cents per question and 2 dollars per conversation.  
- With this agentic approach in the future, they foresee much more DB (possibly) smaller queries than today where we have less queries but (possibly) better written. 
- Agent first tries to understand the question well. Because in most of the cases users do not know what they want and it needs clarifications/precision. That's why a good semantic layer is very important. 
- Some companies are using medallion architecture to structure their data (I kinda liked it)


### Links

- https://getnao.io/
- https://dust.tt/
- https://www.databricks.com/blog/what-is-medallion-architecture
- https://altertable.ai/ (AI-Native Data Platform/warehouse with Always-On Agents, met Sylvain Utard. one of the founders)

Would it be useful to me/to the company? The answer is definitely yes for me. Thanks to this, I'd spend much less time on non-interesting requests. Someone mentioned that this requires a good foundation on data warehouse as well. Since (potentially) more people interacts with data, it should be reliable all the time to everyone. 


### Self-QA
What is rag? They mention a lot
> RAG, or Retrieval-Augmented Generation, is a technique that enhances large language models (LLMs) by allowing them to retrieve and incorporate new information from external data sources before generating responses. 

Mistral is about 100 times less than Claud according to some panelist.