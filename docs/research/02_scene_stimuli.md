# Scene stimuli: natural rooms that measure memory

## Recommendations for this game

No paper prescribes a placement mix for this task. The rules below apply the evidence to it, and the numbers in them are inference. I checked target names and some scale values in the build files, but did not view the renders.

1. **Remove semantic misfits first.** Every target and filler should plausibly belong in the room. Raters judged wrong-scene objects worse than misplaced ones (SCEGRAM). Review: rubber duck, ukulele, suitcase (living room); watering can, alarm clock (kitchen). *Evidence: moderate, 12 raters.*
2. **Build in functional clusters.** Choose large fixed anchors first, then place small objects beside the anchor they are used with (pot by stove). *Evidence: moderate; direct on scene structure, indirect for memory. Draschkow & Võ 2017 had N=10 per experiment.*
3. **Make support and size physically right.** Nothing floats, intersects, or sits on a surface that could not hold it. Use real-world scale. Audit non-uniform or enlarged models, for example the dining table at `(0.6, 0.62, 1.0)` and cans at 1.6 in `build_rooms.py`. *Evidence: moderate; rating and eye-movement data, none on these rooms.*
4. **Do not give targets a uniquely guessable spot.** Place each target where it fits but where several other spots also fit: a jug on the table, counter or shelf, not a kettle on the hob. Suggested mix per room: about 10–12 moderately expected, 2–3 highly expected, 0–2 mildly odd but possible, none impossible. Same mix in every room. *Evidence for the problem: strong (Quent 2022; Ramey 2022). The mix: inference.*
5. **Measure guessability with a no-study group.** About 10–15 people (inference) place the objects in the empty room without seeing the full one. Replace any target whose guesses cluster on its true location, then report participants' error against this baseline. *Evidence: moderate; method precedent, not validated for this game.*
6. **Norm expectancy, then model it.** Rate each object at each target location, and ask participants too at debrief. Include expectancy as a linear and quadratic covariate, because the effect is U-shaped. *Evidence: strong, preregistered (Quent 2022).*
7. **Counterbalance room with condition across participants.** Equate rooms on expectancy, object size in image, salience and edge density as well. Ideally make two layouts per room. *Evidence: moderate; counterbalancing is standard, but I found no published procedure for matched rendered rooms.*
8. **Make targets conceptually distinct and easy to name.** No two targets from one category, within or across rooms. Current overlaps: horse statue, cat statue and carved elephant; antique vase and ceramic vase; alarm clock and mantel clock; teapot, kettle and jug. *Evidence: moderate for item memory; extension to location binding is inference.*
9. **Use a neutral tray cue.** Render each object separately from a standard view, in neutral light, without shadows, and scaled to a fixed box. Never cut tray images from the room render. *Evidence: precedent only (SCEGRAM object-only images); leakage itself is untested.*
10. **Pilot naturalness and render contact properly.** Keep global illumination and contact shadows, render the empty room rather than painting objects out, and leave plausible free spots so removed targets do not leave telltale gaps. Have independent raters score each room and click whatever looks wrong. *Evidence: weak to moderate; gaps and click-rating are inference.*

## Findings

### 1. Scene grammar

Terms vary. Biederman et al. (1982) defined five relations: support and interposition (physical), and probability, position and size (semantic). Võ & Wolfe (2013) instead call an object that misfits the scene's meaning semantic, and an object in an atypical place syntactic. Syntactic violations are mild (toothbrush in the sink) or extreme (hovering).

In SCEGRAM, all violation types were rated less consistent than controls. Semantic violations were rated worse than both syntactic types, and raters varied most on extreme syntax. Both violation types lengthened dwell times.

Hierarchy: scenes contain "phrases", each holding one anchor that predicts the identity and position of nearby local objects (Turini & Võ 2022). Relevant anchors speed search (Boettcher et al. 2018).

Draschkow & Võ (2017) had people build VR rooms of 5 global and 10 local objects. Consistent rooms gave better location recall and faster search, and they shared more repeated object pairings (oven and pot). Performance beat a between-subject baseline, but the consistency benefit could partly reflect guessing (inference).

### 2. Congruency and location memory

Early results conflict: Brewer & Treyens (1981) linked memory to schema expectancy, others favoured atypical items (per Quent et al.). Mandler & Parker (1976) reported that schemas affected spatial memory, not descriptive detail.

Quent et al. (2022) is the closest design: immersive VR kitchen, 20 objects, 45 s study, objects replaced one at a time, 137 adults. Memory was U-shaped against expectancy, lowest for neutral locations. Key points:

- **Guessing is visible.** In the pilot, incorrect placements averaged +40.7 expectancy on a −100 to +100 scale, against +2.90 for correct ones.
- **Control by test design.** Forced-choice foils matched in expectancy removed guessing as an explanation, and the U shape still appeared.
- **Confound.** Kitchen objects first landed at the extremes and non-kitchen objects at neutral spots, so placements were reselected to cover the range for both.

Ramey et al. (2022) found better recall for congruent locations, strongest for new scenes and absent for recollected scenes. Schema mainly fills in when memory fails. Their no-memory baseline is clicks on never-studied scenes. Cockcroft et al. (2022) warn that "schema-irrelevant" controls can still be shaped by schemas, so a neutral placement cannot be assumed neutral.

Trade-off (inference): moderate expectancy limits guessing, but sits at the bottom of the U, so pilot for floor effects.

### 3. Building and validating sets

SCEGRAM is the main model: 62 scenes in six conditions, with objects paired by shape, colour and size and swapped between paired scenes. It adds object-absent and object-only images, a saliency rank check (mean rank above 4.5 in all conditions), and an eye-movement cross-validation. Twelve raters used a 1–6 scale, and the authors tell users to collect their own ratings. Quent's norming collected 400 ratings, one per object-location pair; open materials are at osf.io/4sw2t.

ObScene (Andrade et al. 2023) offers 898 photographic object-scene pairs, with congruency, name-agreement, familiarity and visual-complexity ratings. I found no published whole-room naturalness scale, and no procedure for equating rendered rooms on object-location difficulty. The literature is thin here.

Object counts: 12 (Melcher 2001), 15 (Draschkow et al. 2014; Draschkow & Võ 2017), 20 (Quent 2022). Fifteen targets is in range, though these studies differ in design. Image clutter, indexed by feature congestion, sub-band entropy and edge density, relates to search performance (Henderson et al. 2009). That was search, not memory; using it to equate rooms is inference.

### 4. Object choice

Memory for exemplars fell as more from one category were held, and conceptual distinctiveness predicted this better than perceptual distinctiveness (Konkle et al. 2010). That was item recognition, not location. SCEGRAM recoloured distractors that matched critical objects in other scenes, a useful precedent for avoiding duplicates.

BOSS (Brodeur et al. 2010) applies a name-agreement criterion; THINGSplus (Stoinski et al. 2023) norms real-world size. I found no study of nameability effects on object-location memory in scenes; collecting name agreement in piloting is inference.

### 5. Rendered versus photographed

I found no direct validation of photorealistic renders against photographs for object-location memory. Tatler & Melcher (2007) found better object memory for photographs than non-photographic scenes, and non-photographic scenes that obeyed realistic organisation also affected memory. Grammar effects do appear in rendered material (Võ & Henderson 2009; Draschkow & Võ 2017; Quent 2022), which is support, not equivalence.

SCEGRAM's authors say rendered scenes usually fall short of photographic realism and rarely contain natural clutter, and warn that off-scale objects add a size violation. Cast shadows convey spatial layout (Mamassian et al. 1998), and shadows and interreflections both signal contact (Thompson et al. 1998).

### 6. Cue leakage

I found no study testing tray-cue leakage directly. Closest precedents: SCEGRAM's object-only images, shot on a white background, centred and resized to a fixed box; and its absent images, shot immediately after the present ones to limit lighting changes. Hollingworth (2006) found object memory better when tested in the original scene context, which supports testing in the empty room.

Inference: scene-cut tray images could leak viewpoint and lighting, and their image size could leak depth. Removing a target also removes its shadow and can leave a gap, which an empty image reveals. The no-study group (rule 5) tests this.

## References

- Biederman, Mezzanotte & Rabinowitz (1982). Scene perception: Detecting and judging objects undergoing relational violations. https://www.cs.princeton.edu/courses/archive/spring08/cos598B/Readings/Biederman1982.pdf [secondary source]
- Boettcher et al. (2018). Anchoring visual search in scenes. *J Vision* 18(13):11. [read abstract only] Located through the Frankfurt list: https://www.psychologie.uni-frankfurt.de/120681223/Publications
- Brewer & Treyens (1981). Role of schemata in memory for places. *Cogn Psychol* 13. [secondary source] No page read.
- Brodeur et al. (2010). Bank of Standardized Stimuli. *PLoS ONE* 5(5):e10773. https://pmc.ncbi.nlm.nih.gov/articles/PMC2879426 [read abstract only]
- Cockcroft et al. (2022). Schematic information influences memory and generalisation behaviour for schema-relevant and -irrelevant information. *Cognition* 105203. https://eprints.whiterose.ac.uk/187767/ [read abstract only]
- Draschkow, Wolfe & Võ (2014). Seek and you shall remember. *J Vision* 14(8):10. doi:10.1167/14.8.10 [read full text, via automated summary]
- Draschkow & Võ (2017). Scene grammar shapes the way we interact with objects, strengthens memories, and speeds search. *Sci Rep*. https://pmc.ncbi.nlm.nih.gov/articles/PMC5705766/ [read full text, via automated summary]
- Henderson, Chanceaux & Smith (2009). The influence of clutter on real-world scene search: Evidence from search efficiency and eye movements. *J Vision* 9(1):32. doi:10.1167/9.1.32 [read abstract only]
- Hollingworth (2006). Scene and position specificity in visual memory for objects. https://iro.uiowa.edu/esploro/outputs/journalArticle/Scene-and-position-specificity-in-visual/9984213268702771 [read abstract only]
- Konkle, Brady, Alvarez & Oliva (2010). Conceptual distinctiveness supports detailed visual long-term memory for real-world objects. doi:10.1037/a0019165 [read abstract only]
- Mamassian, Knill & Kersten (1998). The perception of cast shadows. *TiCS* 2(8). https://experts.umn.edu/en/publications/the-perception-of-cast-shadows/ [read abstract only]
- Mandler & Parker (1976). Memory for descriptive and spatial information in complex pictures. doi:10.1037/0278-7393.2.1.38 [read abstract only]
- Melcher (2001). Persistence of visual memory for scenes. *Nature* 412. https://www.nature.com/articles/35086646.pdf [secondary source]
- Andrade, Cipriano & Raposo (2023). ObScene database: Semantic congruency norms for 898 pairs of object-scene pictures. *Behav Res Methods*. doi:10.3758/s13428-023-02181-7 [read abstract only]
- Öhlschläger & Võ (2017, online 2016). SCEGRAM. *Behav Res Methods*. doi:10.3758/s13428-016-0820-3 [read full text, except eye-movement section]
- Quent, Greve & Henson (2022). Shape of U. *Psychol Sci* 33(12). doi:10.1177/09567976221109134 [read full text in part: abstract, method, pilot, Experiment 1 and General Discussion]
- Ramey, Henderson & Yonelinas (2022). Episodic memory processes modulate how schema knowledge is used in spatial memory decisions. *Cognition* 225:105111. doi:10.1016/j.cognition.2022.105111 [read abstract only, plus method excerpts]
- Stoinski, Perkuhn & Hebart (2023). THINGSplus. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10991023/ [read abstract only]
- Tatler & Melcher (2007). Pictures in mind. *Perception* 36(12). doi:10.1068/p5592 [read abstract only]
- Thompson, Shirley, Smits, Kersten & Madison (1998). Visual Glue. Univ. Utah UUCS-98-007. https://users.cs.utah.edu/docs/techreports/1998/pdf/UUCS-98-007.pdf [read abstract only, plus excerpts]
- Turini & Võ (2022). Hierarchical organization of objects in scenes is reflected in mental representations of objects. *Sci Rep* 12:20068. doi:10.1038/s41598-022-24505-x [read abstract only]
- Võ & Henderson (2009). Does gravity matter? *J Vision*. https://core.ac.uk/download/28967803.pdf [secondary source]
- Võ & Wolfe (2013). Differential electrophysiological signatures of semantic and syntactic scene processing. https://www.pubmed.gov/23842954/ [read abstract only]
