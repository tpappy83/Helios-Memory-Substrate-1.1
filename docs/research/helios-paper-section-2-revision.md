# Helios — Revised §2 (Related Work) for NeurIPS 2026 Workshop Submission

**Status:** Splice-in deliverable. Drop-in replacement for the existing §2 of `helios_paper_draft_v1.md` / `.tex`. Tighten the contrast against A-MEM (NeurIPS 2025) and CMA (arXiv:2601.09913) per the Helix subagent's brutal-honest novelty assessment.

**Author note:** the existing §2 understates the proximity to A-MEM. Reviewer 2 of any NeurIPS workshop will flag this; better to surface it ourselves with a sharp differentiation than have it surfaced as a "missing differentiation" rejection ground.

---

## 2 Related Work

LLM-mediated memory systems for long-horizon agents have converged on five settled questions and one open one. The settled: (1) vector embeddings with approximate $k$-NN are the default retrieval primitive [HMN; A-MEM; Voyager; ExpeL; EM-LLM]; (2) hierarchical organization beats flat memory [HMN; GraphRAG; Soar EpMem; R3Mem]; (3) LLMs are viable memory curators [A-MEM; ExpeL; GraphRAG; CMA]; (4) episodic/semantic separation is architecturally useful [Soar EpMem; A-MEM; EM-LLM; CMA]; (5) skills-as-callable-templates extend agentic capability [Voyager; MemGPT function calls]. The open question — and the one Helios addresses — is whether these layers can be jointly disciplined into an immutable-substrate / retrospectively-induced-concepts / compiled-skills architecture without sacrificing recall or scalability. This section maps Helios's contribution against the eight most proximate prior systems.

### 2.1 Substrate-with-induced-attributes: A-MEM is the closest prior art

A-MEM \citep{xu2025amem} is the closest neighbor to Helios's thesis and the work against which our novelty claim must be defended most carefully. A-MEM stores Zettelkasten-style memory notes $m_n = \{\text{content}, \text{context}_n, \text{keywords}_n, \text{tags}_n, \text{embedding}_n\}$; on each new write, the LLM \emph{co-generates} the attributes $\text{context}, \text{keywords}, \text{tags}$ and then \emph{evolves} the top-$k$ nearest existing notes via $m_j^\ast = \text{LLM}_\text{evolve}(m_j, m_n, M_\text{near}^n)$, updating their attributes in place. Empirically A-MEM beats LoCoMo, MemGPT, and MemoryBank baselines on the LoCoMo benchmark by 35–192\% in F1 across six foundation models.

The architectural overlap with Helios is significant: A-MEM has a metadata substrate, LLM-induced concept-like attributes, and dynamic links — that is substrate → concepts → indexes in our framing. We distinguish on three commitments not jointly present in A-MEM:

\begin{enumerate}
  \item \textbf{Substrate immutability.} Helios's $\text{memory\_records}$ table is append-only post-ingest. The raw content, type, importance, timestamp, and metadata blob are frozen. A-MEM's evolve-on-write mutates $\text{context}_j, \text{keywords}_j, \text{tags}_j$ on neighbor notes whenever a new note arrives. The two are different commitments: immutability gives reproducibility, audit trail, and crypto-shredability per record; mutability gives compactness and self-organization. We argue (\S\,4.2) that the audit and reproducibility properties matter more in production deployments where memory is a shared resource across tenants and over time.
  \item \textbf{Retrospective induction.} Helios's concepts are induced \emph{after the fact}, asynchronously, over patterns in the frozen substrate (clustering on metadata + LLM labeling). A-MEM's attributes are generated \emph{at write time}, inline with the note creation. Retrospective induction is what allows Helios to revise concepts under new evidence without rewriting the substrate; A-MEM has no such mechanism. The price is two-stage latency: write-time is cheap, but the user does not see the new concept until the induction worker runs.
  \item \textbf{Skill compilation into prompts.} A-MEM has no explicit skill layer; the dynamic links between notes serve as a retrieval-time signal but not as a callable abstraction. Helios's skills materialize as $(\text{induced\_concept}, \text{query\_template}, \text{success\_criteria})$ triples that compile directly into the system prompt of $\text{llm\_rerank}$ and $\text{llm\_classify}$. This is closer to Voyager's vector library of code skills than to A-MEM — and we draw that distinction next.
\end{enumerate}

\paragraph{If A-MEM had skills.} An obvious reviewer question: could A-MEM be extended with a skill layer? In principle yes, but its write-time evolution is incompatible with skill compilation. Skills require concepts to be stable references; if neighbor-note attributes update on each write, the skill template grounded in those attributes drifts continuously. Helios's immutable-substrate / retrospective-induction discipline is what makes the skill layer tractable.

### 2.2 Skill libraries: Voyager defines the upper bound, but skills emerge differently

Voyager \citep{wang2023voyager} introduced LLM-induced skill libraries: a vector database $S = \{(\text{emb}(\text{desc}_i), \text{code}_i)\}$ retrieved by cosine similarity, with each skill itself a chunk of executable code synthesized by an iterative prompt-execute-verify loop in Minecraft. Voyager's library produces 3.3$\times$ more unique items and traverses the tech tree 15.3$\times$ faster than ReAct, Reflexion, or AutoGPT baselines.

Helios's skill layer is functionally analogous (callable, retrievable, induced) but emerges from a different mechanism. Voyager's skills arise from an embodied trial-and-error curriculum in an environment; Helios's skills arise from patterns over user-interaction substrate (queries that exhibit high locality with respect to a single induced concept, per the locality threshold $\lambda_{\text{loc}}$ in \S\,3.4). The two mechanisms produce skills with different epistemic warrant: Voyager skills are environmentally verified (the code runs or it doesn't); Helios skills are statistically warranted (the pattern recurs across users, against an induced concept). Both have failure modes, and we acknowledge ours in \S\,6.

If the reviewer's concern is "are Helios skills just Voyager skills with different inputs?" the answer is no: Voyager skills are programs whose semantics are defined by the environment's reaction to them; Helios skills are prompt fragments whose semantics are defined by their effect on downstream LLM ranking and classification. The latter is closer to the "in-context-learning prompt template" literature than to code generation.

### 2.3 Architectural class membership: Helios is a concrete CMA instance

The Continuum Memory Architectures preprint \citep{cma2026} names the architectural class Helios sits within. CMA specifies a lifecycle: ingest (metadata), retrieval (multi-factor ranking), mutation (reinforcement / suppression / co-link), and consolidation (replay / abstraction / gist extraction). It explicitly admits multiple concrete instantiations and does not prescribe one.

We argue Helios is most honestly framed as \textbf{a concrete CMA instantiation} with three architectural commitments that the CMA preprint leaves unspecified:

\begin{itemize}
  \item Where CMA permits substrate mutation as part of "reinforcement," Helios restricts mutation to the indexes derived from the substrate, never the substrate itself.
  \item Where CMA describes consolidation as a generic abstraction operation, Helios specifies consolidation as the concept-induction worker that runs asynchronously over frozen substrate.
  \item Where CMA is silent on agentic affordance, Helios adds the skill-compilation layer.
\end{itemize}

This framing has two advantages. First, it accepts that the architectural class is not Helios's invention — that fight cannot be won against a preprint of CMA's scope. Second, it makes Helios's specific contribution concrete and falsifiable: each of the three commitments above is an empirically testable design decision against the CMA superclass. Section 5 proposes pilots for each.

### 2.4 Other proximate work

\paragraph{Graph RAG \citep{graphrag2024}.} Microsoft's GraphRAG materializes Leiden hierarchical clusters as community summaries and runs map-reduce LLM queries over the entire community hierarchy. Architecturally this is "substrate → indexes" but with the substrate being LLM-extracted entities and relations rather than user interactions, and with no skill layer. The hierarchy is fixed at index time; there is no equivalent of Helios's retrospective concept induction.

\paragraph{MemGPT / Letta \citep{packer2024memgpt}.} MemGPT addresses memory \emph{capacity} via OS-style paging between main and external context, with the LLM emitting function calls to page data in. This is orthogonal to our work: MemGPT specifies how to fit more memory into a fixed context window; Helios specifies how to organize memory across stages of induction. The two can compose — a deployment could use Helios's substrate / concepts / skills with MemGPT-style paging at the prompt-assembly stage — but neither subsumes the other.

\paragraph{ExpeL \citep{zhao2024expel}.} ExpeL extracts insights from trajectory pools via gradient-free LLM operations (\{ADD, EDIT, UPVOTE, DOWNVOTE\}), retrieved by embedding similarity. The closest analog to Helios's concept induction. The principal distinction: ExpeL's insights are a flat list, not organized hierarchically, and ExpeL has no separate skill compilation. We borrow ExpeL's gradient-free LLM-as-curator motif and discipline it into Helios's layered architecture.

\paragraph{Hierarchical Memory Networks \citep{chandar2016hmn} and Soar EpMem \citep{derbinsky2009epmem}.} HMN is a neural memory access mechanism (MIPS-based $k$-selection over hierarchically organized memory cells), not a substrate / concept / skill architecture. Soar EpMem is the deepest cognitive-architecture prior art for Helios, with substrate, semantic memory, and procedural memory ($\approx$ skills). Soar's semantic memory is hand-authored, however; Helios's is LLM-induced from substrate. The induction step is the novelty boundary.

\paragraph{Infinite-context / virtual-context work \citep{emllm2024; memory3; r3mem}.} Recent infinite-context systems (EM-LLM, Memory$_3$, R$_3$Mem) extend the KV cache substrate, not the agentic memory architecture. They are orthogonal to Helios at the architectural layer: Helios sits one level above, taking the LLM's effective context as a black box and deciding what to put in it.

### 2.5 Summary: Helios's defensible novelty

Helios is best positioned as a concrete CMA-class system with three architectural commitments not jointly present in any single prior system:

\begin{enumerate}
  \item \textbf{Immutable substrate} (vs. A-MEM's evolve-on-write attribute generation; vs. CMA's permitted substrate mutation).
  \item \textbf{Retrospective concept induction} over the frozen substrate (vs. A-MEM's write-time co-generation; vs. CMA's unspecified consolidation mechanism).
  \item \textbf{Callable skill templates compiled into LLM rerank/classify prompts} (vs. Voyager's standalone code skills; absent in CMA, A-MEM, GraphRAG, MemGPT, ExpeL).
\end{enumerate}

We do not claim novelty against the CMA class itself; that claim is unwinnable in peer review. We claim novelty within the class via the joint commitment above and via the empirical instantiation reported in \S\,5. To our knowledge no prior system has shipped all three commitments simultaneously, and the design decisions they entail (audit-preserving substrate, two-stage write→induce latency, prompt-compilation rather than tool-calling for skill invocation) are the load-bearing contributions of this paper.

---

## BibTeX additions (to splice into your paper's references.bib)

```bibtex
@inproceedings{xu2025amem,
  title={{A-MEM}: Agentic Memory for {LLM} Agents},
  author={Xu, Wei and Liang, Zhaoyang and Mei, Kai and Gao, Hangyu and Tan, Juyuan and Zhang, Yongfeng},
  booktitle={Advances in Neural Information Processing Systems (NeurIPS)},
  year={2025},
  note={\url{https://arxiv.org/abs/2502.12110}}
}

@article{cma2026,
  title={Continuum Memory Architectures for Long-Horizon {LLM} Agents},
  author={(Author list not yet confirmed in published metadata)},
  journal={arXiv preprint arXiv:2601.09913},
  year={2026},
  note={Preprint; peer-review status unconfirmed as of 2026-05-16. \textbf{Verify before camera-ready.}}
}

@article{wang2023voyager,
  title={Voyager: An Open-Ended Embodied Agent with Large Language Models},
  author={Wang, Guanzhi and Xie, Yuqi and Jiang, Yunfan and Mandlekar, Ajay and Xiao, Chaowei and Zhu, Yuke and Fan, Linxi and Anandkumar, Anima},
  journal={Transactions on Machine Learning Research (TMLR)},
  year={2024},
  note={\url{https://arxiv.org/abs/2305.16291}}
}

@inproceedings{zhao2024expel,
  title={{ExpeL}: {LLM} Agents Are Experiential Learners},
  author={Zhao, Andrew and Huang, Daniel and Xu, Quentin and Lin, Matthieu and Liu, Yong-Jin and Huang, Gao},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence},
  year={2024},
  note={\url{https://arxiv.org/abs/2308.10144}}
}

@inproceedings{graphrag2024,
  title={From Local to Global: A Graph {RAG} Approach to Query-Focused Summarization},
  author={Edge, Darren and Trinh, Ha and Cheng, Newman and Bradley, Joshua and Chao, Alex and Mody, Apurva and Truitt, Steven and Larson, Jonathan},
  journal={arXiv preprint arXiv:2404.16130},
  year={2024}
}

@inproceedings{packer2024memgpt,
  title={{MemGPT}: Towards {LLMs} as Operating Systems},
  author={Packer, Charles and Wooders, Sarah and Lin, Kevin and Fang, Vivian and Patil, Shishir G and Stoica, Ion and Gonzalez, Joseph E},
  booktitle={Proceedings of the Conference on Language Modeling (COLM)},
  year={2024},
  note={\url{https://arxiv.org/abs/2310.08560}}
}

@inproceedings{chandar2016hmn,
  title={Hierarchical Memory Networks},
  author={Chandar, Sarath and Ahn, Sungjin and Larochelle, Hugo and Vincent, Pascal and Tesauro, Gerald and Bengio, Yoshua},
  booktitle={International Conference on Learning Representations Workshop},
  year={2017},
  note={\url{https://arxiv.org/abs/1605.07427}}
}

@inproceedings{derbinsky2009epmem,
  title={Efficiently Implementing Episodic Memory},
  author={Derbinsky, Nate and Laird, John E},
  booktitle={Case-Based Reasoning Research and Development (ICCBR)},
  series={LNCS},
  volume={5650},
  pages={403--417},
  publisher={Springer},
  year={2009}
}
```

---

## Notes for the authors

- **Bibliographic confidence:** Author orderings above are ~95% confidence from the Helix subagent's research. Re-verify against the venue's official proceedings before camera-ready. Specifically: A-MEM author list (Xu et al. NeurIPS 2025) must be confirmed exactly as published; the CMA preprint author list was not extracted in the research pass and should be filled in from arXiv directly.
- **Tone calibration:** the existing §2 understates A-MEM's proximity. The revised version above explicitly names A-MEM as "the closest prior art" — this is more defensible in peer review than burying the comparison. Reviewer 2 will respect honest contrast more than understated novelty.
- **Length budget:** the revised §2 above is ~1,700 words in academic prose. The existing §2 in `helios_paper_draft_v1.md` was ~1,200 words (per the prior memory). The 500-word addition is justified by the depth of A-MEM contrast; if length budget is tight, the §2.4 "Other proximate work" subsection can be compressed to a single paragraph.
- **Camera-ready open items:** (1) confirm A-MEM bibliographic line; (2) confirm CMA's peer-review status — if rejected, soften the "concrete CMA instantiation" framing; (3) if A-MEM published an extension paper between submission and camera-ready, add it.
