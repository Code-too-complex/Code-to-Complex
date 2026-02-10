# Code-to-Complex
The scripts in this repository are helper scripts to process binder structures and sequences from the pdb putput of RFdiffusion or BindCraft to processed DNA sequences for integration in pET-28a(+) (6xHis tag in N') or PET29a (6x His tag in C').

Scripts are intended to be executed in order of the initial number of the script.

Stage 1: Consolidation & Orientation
The pipeline begins by scanning deep subdirectories to find "Accepted" design models. It pulls these scattered files into a central location and standardizes their 3D orientation. By aligning every design to a specific reference (the LRR domain of RXFP1), it ensures that one can compare all binding interfaces from the same perspective.

Stage 2: Statistical Intelligence & Ranking
Once aligned, the system aggregates the confidence metrics (such as iPTM and iPAE). It performs a hierarchical sort to identify which designs have the best binding confidence and the highest structural confidence. 

Stage 3: Biological Feasibility Filtering
This stage acts as a "sanity check" for the real world. It analyzes the proximity of  designs to a glycosylation site. Any design that is structurally sound but would physically clash with the sugar molecules represented by a manually placed water molecule is discarded.

Stage 4: Interactive Tag Placement Analysis
Before moving to synthesis, the pipeline evaluates the accessibility of the protein termini. It calculates whether the N-terminus or C-terminus is more "buried" or "exposed" within the design. This allows you to interactively decide where to place the His-tag for purification, ensuring the tag doesn't interfere with the binding interface or lead to misfolding.

Stage 5: Redundancy & Uniqueness Control
Because computational design often produces similar solutions, the pipeline compares the top designs against one another. It filters out "doublets" (redundant sequences or structures) based in the seed number.

Stage 6: Genetic Architecture & Cloning Logic
In the final transition from digital to physical, the 3D models are translated into 1-letter amino acid sequences. The pipeline then "engineers" the DNA by:

Standardizing the names for tube labels.

Adding specific Purification Tags (6xHis), and Stop Codons if needed.

Removes redundant start codons for N' tagged binders. 

Applying DNA Padding to ensure short sequences meet the minimum length requirements for TWIST synthesis providers (300bp).
