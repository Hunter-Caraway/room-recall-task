# Object-location paradigms: evidence for the colored noise memory task

## Recommendations for this game

"Inference" means my reasoning. Key gap: I found **no paper that tests sprite perspective or scale as a retrieval cue**, so items 1 and 2 extrapolate from design practice.

1. **Neutralize the tray sprites.** Render each object alone from one fixed canonical camera, at one standard tray size, not cut from the room. *Evidence:* Object Relocation shows objects in a row above a flat frame (Kessels 1999). Murcia-López & Steed (2016) chose rotationally symmetric stools, "providing no orientation cues". Strength: direct test absent; the fix itself is inference.
2. **Measure the leak with people who never saw the room.** Have a pilot group (about 8-12, my guess) place objects with no study phase, using old and new sprites. Compare x error with y error, since inference says depth cues should mostly help y. *Evidence:* Mandler & Parker (1976) compared reconstructions with people who had not seen the pictures. Strength: moderate. This also gives item 3's guessing baseline.
3. **Keep 1/0 scoring and add continuous distance.** They coexist: Pertzov (2012) reports absolute error and within-threshold percent together. Pre-specify one as primary. I suggest distance, because it holds more information (inference). Strength: strong as common practice; no head-to-head test of tolerance against continuous scoring found.
4. **Add a swap measure.** Score each placement against the nearest other target's original spot, with a shuffled chance level. *Evidence:* Pertzov (2012), Watson (2013), Grogan (2020). Strength: strong. Keep targets at least 2x tolerance apart so a placement cannot count for two targets (inference, based on Pertzov's 5° threshold and 10° spacing).
5. **Add a filled retention interval of 30 s to 2 min.** Use a nonspatial filler. *Evidence:* Castegnaro (2022) used about 2 min. Strength: moderate. No head-to-head study of filler length found.
6. **Fix and log noise timing.** Noise at encoding is the most tested timing, and Herweg & Bunzeck (2015) show that timing changes results. If noise runs through study and test, the phases cannot be separated (inference). Calibrate the level at the ear, about 65-78 dB as in published work. Strength: moderate.
7. **Control room-schema guessing.** Realistic rooms let knowledge place objects: scene organization strongly affected location memory (Mandler & Parker 1976), and consistent arrangements were recalled better (Draschkow & Võ 2017). Pick objects with several plausible spots; use item 2's per-object baseline. Strength: moderate.
8. **Randomize tray order per room and participant; keep the free tray.** Pertzov (2012) re-presented all objects at random positions with free order. Keep logging `placement_order`. Strength: moderate.
9. **Do not rescale objects during dragging, for now.** No study of depth-contingent rescaling found. A constant-size sprite or a drop marker is simplest (inference). Score from a fixed anchor point. Strength: none direct.
10. **Analyze with mixed models, not per-person mixture fits.** Grogan simulated 100 trials per agent, while this design yields far fewer (inference). Grogan also supports hierarchical fitting. Report results by depth: 5% of image width covers more floor at the back (inference). Strength: moderate.

**Expectation to state plainly:** in non-ADHD groups, white and pink noise had a small negative pooled effect (g = -0.212; Nigg 2024). If an effect of about 0.25 applied as dz, 35 participants would give roughly one-third power (my rough calculation).

## Findings

### Q1. How the experiments run

- **Postma & de Haan (1996):** displays studied for 30 s; tasks were relocating objects, reconstructing positions, or assigning objects to marked positions.
- **Object Relocation (Kessels 1999):** flat frame with assigned locations, variable study time, optional delay, objects in a row above the frame. Click or drag (search excerpt).
- **Location Learning Test:** the revised version has five learning trials and 30-min delayed recall, scored by displacement. A modified version used shorter presentation and longer delay to avoid ceiling effects (Kessels 2004, 2006).
- **Pertzov (2012):** natural objects, set sizes 1-5, 1 s per object, 1 s or 4 s blank delay, touchscreen dragging, 150-250 trials in Experiment 1.
- **Watson (2013):** real objects, set sizes 2-5, roughly 4 s delay.
- **Memory Island:** a water-maze-style navigation test scored by time in the target quadrant (Piper 2010), not a relocation task.
- **Rendered or VR rooms:**
  - Draschkow & Võ (2017): 15 objects, 16 rooms, 10 participants per experiment, surprise recall, error in metres.
  - Castegnaro (2022): 4 objects per environment, 3 environments, shown sequentially, about 2 min delay.
  - Huffman (2025): 3 objects, placed by raycast.
  - Helbing (2020): 3D location memory after search or memorization (abstract only).

Thin spot: I found no published drag-from-tray task in photorealistic 2D rooms with 15 objects.

### Q2. Stopping the cue leaking location

The literature is nearly silent on this exact problem. Designs mostly avoid it (last column is inference):

| Design | What the test object shows | Why perspective is not a cue |
|---|---|---|
| Flat frame, row of objects (Kessels 1999) | Object in a row above frame | No depth layout (inference) |
| Random-position test (Pertzov 2012) | Objects at new random spots, free order | No scene depth |
| Immersive VR (Draschkow 2017; Castegnaro 2022) | 3D objects in a 3D room | Projection follows position and view |
| Physical objects (Murcia-López & Steed 2016) | Identical symmetric stools | Designed to give no orientation cue |

Related evidence:

- Segen et al. (2021) rendered the test from a 20° shifted camera so that 3D location, not image position, had to be used. A shifted test view is a possible stronger fix, but it needs new renders and new scoring (inference).
- Mandler & Parker (1976) found that memory for size and orientation survives well over a week.
- I found no study of size adjusted during drag, or of labels replacing images.

### Q3. Scoring

- **Absolute displacement:** the standard measure (LLT total displacement; Castegnaro's absolute distance error; Murcia-López's placement error).
- **Threshold scoring:** Pertzov counted within 5° as correct, alongside absolute error. No source I read says a fixed tolerance is invalid.
- **Swaps:** Pertzov defined a swap as a report within threshold of another object's original location. Nearest-object scoring removed the delay x set-size interaction. Watson found misplacement scores alone could overstate spatial deficits.
- **Mixture models:** Grogan's 2D model separates imprecision, misbinding and guessing. Response-sampled guessing fit better than uniform guessing. Richter (2016) applied mixture modelling to long-term memory, separating success from precision.
- **Guessing baselines, three located options:**
  1. Keep each response's distance and randomize its angle within display limits, then compute the chance swap rate (Pertzov).
  2. Compare with another participant's placements of the same object (Draschkow & Võ).
  3. Compare with people who never saw the display (Mandler & Parker).

  For 1/0 scoring, chance is the proportion of baseline placements inside tolerance (inference).

### Q4. Retention interval

Practice varies widely: 1-4 s blank (Pertzov), about 4 s (Watson), 10 s between encoding and retrieval (Richter), about 2 min (Castegnaro), 30 min delayed recall (LLT).

Pertzov found error grew from 1 s to 4 s. Jeneson (2010) found that patients with medial temporal damage matched controls on few object-location pairs at a 1 s delay, then showed an abrupt drop at larger set sizes. So 15 objects likely exceeds working memory regardless of delay, with a working-memory component for some items (inference).

I found no study that directly tests iconic memory in this paradigm. Huffman describes seconds-long retention as engaging working memory. Without a filler, assume mixed working and long-term memory (inference).

### Q5. Noise and memory

| Study | Sample and design | Noise timing | Level | Blocks | Memory test | Result |
|---|---|---|---|---|---|---|
| Söderlund 2010 | 51 pupils aged 11-12; noise within, attention between | Encoding only | 78 dB white | Alternating lists, about 100 s; orders counterbalanced | Immediate free recall of verb-noun sentences | Helped inattentive (n = 10), hurt attentive; r = .378 |
| Rausch 2014 | Behavioral and fMRI; healthy adults | Encoding | Not in abstract | Not in abstract | Scene recognition | "Slightly" improved |
| Herweg & Bunzeck 2015 | 167 adults, 5 experiments; within | Varied | About 70 dB white | Trial-wise or 3-4 min blocks | Change detection; recognition at 40 min | Maintenance noise impaired WM (p = .012); other timings null; encoding did not change recognition |
| Angwin 2017 | 80 adults; between | Learning phases | 70 dB(A) white, calibrated on artificial ear | 5 phases, one session | Word-object recall | Noise group better over time |
| Awada 2022 | 40 adults; within, Latin square | Continuous | 45 and 65 dB white vs ambient | About 2.5 h total | Two-back | 65 dB: 66.38% vs ambient 64.26%; d = .46 |
| Papalambros 2017 | 13 older adults; randomized crossover | Pink pulses in sleep | 30-50 dB | 2 nights | Word pairs | +9.2 vs +3.1 words (p = .02); not comparable with waking noise |

Nigg (2024) pooled 13 ADHD-range studies (g = 0.249) and found negative effects in comparison groups. It identified **no brown noise studies**. My searches found no behavioral memory study of brown noise (only a 7-person EEG study, Kato 2017) and **no object-location study with colored noise**. Waking pink noise evidence on memory also appears thin.

## References

"[read full text]" means I retrieved the full text and read its relevant sections, directly or through an automated page summary, not cover to cover.

- Angwin AJ, et al. (2017). White noise enhances new-word learning in healthy adults. doi:10.1038/s41598-017-13383-3 [read full text]
- ASSBI. Location Learning Test (publisher page). https://assbi.com.au/Location-Learning-Test [secondary source]
- Awada M, et al. (2022). Cognitive performance, creativity and stress levels of neurotypical young adults under different white noise levels. doi:10.1038/s41598-022-18862-w [read full text]
- Castegnaro A, et al. (2022). Assessing mild cognitive impairment using object-location memory in immersive virtual environments. doi:10.1002/hipo.23458 [read full text]
- Draschkow D, Võ ML (2017). Scene grammar shapes the way we interact with objects, strengthens memories, and speeds search. doi:10.1038/s41598-017-16739-x [read full text]
- Grogan JP, et al. (2020). A new toolbox to distinguish the sources of spatial memory error. doi:10.1167/jov.20.13.6 [read full text]
- Helbing J, Draschkow D, Võ ML (2020). Search superiority: Goal-directed attentional allocation creates more reliable incidental identity and location memory than explicit encoding in naturalistic virtual environments. doi:10.1016/j.cognition.2019.104147 [read abstract only]
- Herweg NA, Bunzeck N (2015). Differential effects of white noise in cognitive and perceptual tasks. doi:10.3389/fpsyg.2015.01639 [read full text]
- Huffman DJ, et al. (2025). Another Brick in the Wall? A Null Effect of Boundaries on Spatial Memory Judgments in a Novel, Highly Immersive, First-Person Object-Placement Task. Proc. CogSci. https://journalpub.escholarship.org/cognitivesciencesociety/article/49889/galley/37851/download [read full text]
- Jeneson A, Mauldin KN, Squire LR (2010). Intact working memory for relational information after medial temporal lobe damage. doi:10.1523/jneurosci.2895-10.2010 [read abstract only]
- Kato, et al. (2017). Oscillatory Neural Activity during Performance of a Cognitive Task in the Presence of Fluctuating Ambient Noise. doi:10.1587/transinf.2016EDP7300 [secondary source]
- Kessels RP, Postma A, de Haan EH (1999). Object Relocation: a program for setting up, running, and analyzing experiments on memory for object locations. doi:10.3758/bf03200721 [read abstract only; drag detail from search excerpt]
- Kessels RP, et al. (2004). The Location Learning Test as a measure of spatial memory (in Dutch). PMID 15478319 [read abstract only]
- Kessels RP, et al. (2006). The modified Location Learning Test: norms. doi:10.1016/j.acn.2006.06.015 [read abstract only]
- Mandler JM, Parker RE (1976). Memory for descriptive and spatial information in complex pictures. doi:10.1037/0278-7393.2.1.38 [read abstract only]
- Murcia-López M, Steed A (2016). The Effect of Environmental Features, Self-Avatar, and Immersion on Object Location Memory in Virtual Environments. doi:10.3389/fict.2016.00024 [read full text]
- Nigg JT, et al. (2024). Systematic Review and Meta-Analysis: Do White Noise or Pink Noise Help With Task Performance in Youth With ADHD or With Elevated Attention Problems? doi:10.1016/j.jaac.2023.12.014 [read abstract only]
- Papalambros NA, et al. (2017). Acoustic Enhancement of Sleep Slow Oscillations and Concomitant Memory Improvement in Older Adults. doi:10.3389/fnhum.2017.00109 [read full text]
- Pertzov Y, et al. (2012). Forgetting what was where: the fragility of object-location binding. doi:10.1371/journal.pone.0048214 [read full text]
- Piper BJ, et al. (2010). The use and validation of the spatial navigation Memory Island test in primary school children. doi:10.1016/j.bbr.2010.02.040 [read abstract only]
- Postma A, de Haan EH (1996). What was where? Memory for object locations. doi:10.1080/713755605 [read abstract only]
- Rausch, Bauch, Bunzeck (2014). White noise improves learning by modulating activity in dopaminergic midbrain regions and right superior temporal sulcus. doi:10.1162/jocn_a_00537 [read abstract only]
- Richter FR, et al. (2016). Distinct neural mechanisms underlie the success, precision, and vividness of episodic memory. doi:10.7554/eLife.18260 [read full text]
- Segen V, et al. (2021). Perspective taking and systematic biases in object location memory. doi:10.3758/s13414-021-02243-y [read full text]
- Söderlund GBW, et al. (2010). The effects of background white noise on memory performance in inattentive school children. doi:10.1186/1744-9081-6-55 [read full text]
- Watson PD, et al. (2013). Spatial reconstruction by patients with hippocampal damage is dominated by relational memory errors. doi:10.1002/hipo.22115 [read full text]
