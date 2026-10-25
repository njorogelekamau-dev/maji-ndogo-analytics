![portfolio-checks](https://github.com/njorogelekamau-dev/maji-ndogo-analytics/actions/workflows/portfolio-checks.yml/badge.svg)

# Crop Decision Support System — Operations Manual

**Module 5 · Classification DSS** · Maji Ndogo Ministry of Agriculture
**Written for:** District Agricultural Officers (DAOs) who prepare planting advice and field-inspection lists
**Author:** Njoroge Kamau · **Version:** 1.0 · October 2026

These are standing instructions. They tell you when to follow the system, when to check it, and when to overrule it. The numbers come from my own runs of the module notebooks. The notebooks, the survey database and the trained models are not published with this manual.

---

## 1. Purpose & scope

The system answers two questions about a field in the Maji Ndogo survey registry. **First, which crop should be planted here?** It suggests one of eight crops (banana, cassava, coffee, maize, potato, rice, tea, wheat) from ten measured conditions: elevation, rainfall, minimum, maximum and average temperature, soil fertility, pH, pollution level, slope and plot size. **Second, is this field heavily polluted?** It flags fields whose pollution score may be above 0.7. You use the first answer to prepare planting advice for farmers. You use the second to decide which fields to inspect.

**Do not use this system for:**

- fields outside the surveyed area, or with conditions outside the range the survey recorded;
- crops that are not on the list of eight;
- fields with any of the ten measurements missing;
- forecasting yield, since it predicts a crop name, not a harvest;
- clearing a field as safe from pollution;
- any decision about subsidies, loans, land allocation or compliance.

The system learned which crops farmers *currently grow* on fields like this one, not which crop *yields best*. Its answer is a starting point for your advice, never the advice itself.

## 2. How the system decides

**Crop recommendations.** Picture 100 experienced officers. Each one studied a different random handful of past survey fields and wrote a checklist of yes/no questions, such as "Is rainfall above 1,300 mm? Is soil pH below 5.0?". When you enter a new field, each officer works through their own checklist and names a crop. The system reports the crop that got the most votes.

Because each officer saw different fields, one officer's bad habit gets outvoted by the others. That makes the system steadier than any single checklist, but it is no smarter than the past fields it learned from.

Rare crops were a problem during training: there are five wheat fields for every rice field. To stop the system simply saying "wheat", I copied the rarer crops' fields until every crop had the same number of examples. That fixed the imbalance. As Section 5 explains, it also made the system look far better on paper than it really is.

**Pollution flags.** A separate, simpler calculator weighs nine of the same conditions (everything except the pollution reading itself) and gives a probability that the field is heavily polluted. A field is flagged when that probability passes a set threshold. Section 4 explains why this calculator should not be relied on.

## 3. Trust tiers

Each crop's tier comes from its **F1 score on fields the system had never seen**. F1 is a single number that is high only when two things are true: the system is usually right when it names that crop, *and* it rarely misses real fields of that crop. The headline 84% accuracy in the notebook is **not** used here. It was measured on test fields that were mostly copies of fields the system had already studied (see Section 5, failure mode A). On genuinely new fields, overall accuracy is 43%.

![Per-crop confidence on unseen fields, with trust tiers](figures/fig-01-trust-tiers.png)

| Crop | Tier | What you do | Evidence: F1 on unseen fields (notebook figure in brackets) |
| :--- | :--- | :--- | :--- |
| tea | **Spot-check** | Advise tea, but before you advise, confirm soil pH on site for 1 field in 5. If pH is above 5.0, treat it as **Second opinion**. | 0.69 (0.91). When it says tea it is right 71% of the time. |
| potato | **Second opinion** | Treat it as a shortlist. Compare with maize and wheat (its main mix-ups, Fig 3) and with local knowledge before advising. | 0.48 (0.83) |
| coffee | **Second opinion** | Treat it as a shortlist. Compare with banana and wheat before advising. | 0.43 (0.87) |
| wheat | **Human review** | Do not pass to the farmer. Refer the field to the district crop specialist. | 0.397 (0.42). Misses 65% of real wheat fields. |
| rice | **Human review** | Do not pass to the farmer. Refer the field to the district crop specialist. | 0.32 (0.94) |
| banana | **Human review** | Do not pass to the farmer. Refer the field to the district crop specialist. | 0.30 (0.86) |
| cassava | **Human review** | Do not pass to the farmer. Refer the field to the district crop specialist. | 0.30 (0.85) |
| maize | **Human review** | Do not pass to the farmer. Refer the field to the district crop specialist. | 0.20 (0.88) |

**Where I drew the lines, and why:**

- **Direct trust (F1 ≥ 0.80): no crop qualifies today.** Acting without any check means a wrong answer costs a farmer a whole season. I will only accept that risk when the system is wrong about 1 time in 5 or less.
- **Spot-check (0.60–0.80).** At this level most answers are right, so checking every field would waste visits. A 1-in-5 site check costs about half a day per check and catches the cases where the system drifts.
- **Human review (below 0.40).** The system's own average F1 across all eight crops is 0.39. A crop that scores below the system's average gets a person, not the system.
- **Second opinion (0.40–0.60).** Everything between those two lines.

Wheat sits just under the 0.40 line, at 0.397. I kept it in Human review rather than round it up, because it is also the crop the system misses most often.

## 4. Pollution audit protocol

**What the evidence shows.** The pollution model never gives any field a probability above 0.12. At the notebook's default threshold of 0.5, and at the lower audit threshold of 0.3, it flags **zero fields** and catches none of the 70 heavily polluted fields in the test set. Overall it looks 94% accurate only because 94% of fields are clean, so calling every field "clean" scores 94% without catching anything. The summary table in the notebook (precision about 0.60, recall about 0.80 at 0.3) does not match what the code actually produces, and I do not rely on it.

![Pollution audit threshold trade-off](figures/fig-04-threshold-tradeoff.png)

**Operating threshold: 0.06, used only to order the sampling queue.** At 0.06 the model catches 50 of the 70 polluted test fields (71%). The cost is 725 flags out of 1,131 fields, which is **13.5 false alarms for every real catch**. Choosing fields at random would give about 15 false alarms per catch, so the model is only slightly better than chance.

I accept that many false alarms because missing a contaminated field can damage soil, crops and people for years, while a false alarm costs one soil test. But the model is too weak to be the control, so the measured reading comes first.

**Procedure:**

1. **Measured fields first.** For every field with a recorded pollution reading, flag it if the reading is above **0.7**. This is the exact condition the model tries to predict, and a measurement always beats a prediction.
2. **Unmeasured fields.** Run the model and flag every field at or above **0.06**. Use the flag list only to decide *which fields to sample first*. Never use it to decide that a field is clean.
3. **When a field is flagged:**
   - suspend its crop recommendation;
   - tell the farmer not to plant food crops until the result is in;
   - book a soil sample within **10 working days**.
4. **Lab result above 0.7.** Record the field as confirmed polluted and escalate to the Water & Environment unit the same week. Leave the crop recommendation suspended.
5. **Lab result 0.7 or below.** Clear the flag, restore the crop recommendation, and record the false alarm.
6. **When you disagree with the model,** your observation wins. Signs that a field may be polluted even without a flag include visible runoff, dead vegetation, or nearby mining or industrial discharge. If you see any of these, request a sample anyway and write down why. If you think a flag is wrong, still take the sample. Do not clear a flag on judgement alone.

**Who owns the number.** Only the Ministry analytics lead can change the 0.06 threshold. District officers cannot. It is reviewed whenever the model is retrained, whenever a district reports a polluted field the model missed, and every quarter in any case.

## 5. Known failure modes

**A. The notebook's headline scores are inflated.** The rare crops were copied *before* the fields were split into "study" and "test" sets. As a result, most test fields were copies of fields the system had already studied: 99% for rice, 95% for maize, 83% for banana. The system was being tested on its own homework. Wheat was never copied, so it is the only crop scored entirely on new fields. That is the real reason the most common crop looked like the least trustworthy one.
**Override:** use only the unseen-field scores in Section 3. Treat any "84% accurate" claim as wrong until the system is re-tested properly.

![Share of test rows already seen during training](figures/fig-02-evaluation-leakage.png)

![Confusion matrix on unseen fields](figures/fig-03-confusion-matrix.png)

**B. Wheat is under-recommended and gets scattered across other crops.** The system identifies only 35% of real wheat fields. Wheat grows at middle rainfall (median about 970 mm). That puts it between the dry-land crops, potato and maize (about 640 mm), and the wet crops, cassava, tea, coffee, rice and banana (1,200–1,670 mm). Wheat fields therefore get called potato (19%), maize (12%), cassava (9%) or banana (8%). In the other direction, 30% of real maize fields and 21% of potato fields are called wheat.
**Override:** if a field gets 900–1,100 mm of rain and the system says potato or maize, raise wheat with the crop specialist before you advise.

**C. Maize and potato are hard to tell apart.** 41% of real maize fields are recommended potato, and 21% of potato fields are recommended maize. Both are dry-land crops at similar temperatures. The main difference is soil pH: maize fields have a median pH of 6.1 and potato fields 5.4.
**Override:** for any maize-or-potato answer, test soil pH. Treat the answer as uncertain if pH falls between 5.4 and 6.1.

**D. Cassava and tea get mixed up on acidic soils.** 29% of cassava fields are recommended tea, and 15% of tea fields are recommended cassava. Both grow on the most acidic soils in the survey (median pH 5.2 for cassava, 4.7 for tea).
**Override:** this is why tea is spot-checked by pH (Section 3). Above pH 5.0, do not accept a tea recommendation without review.

**E. Rice is mostly called banana.** Banana, coffee and rice all grow at the highest rainfall (about 1,600–1,670 mm) with similar pH. 45% of real rice fields are recommended banana, and 25% of banana fields are recommended coffee. Rice also has the fewest real examples in the survey (265 fields). Its notebook score of 0.94 falls to 0.32 on new fields.
**Override:** never act on a rice, banana or coffee recommendation for a high-rainfall field without the crop specialist.

**F. It learned what farmers grow, not what grows best.** The training data records the crop each farmer chose. Where a field's own yield history disagrees with the system, the yield history wins.

**G. The pollution model is close to blind.** See Section 4. A field with no flag is **not** a clean field.

**H. Readings outside the surveyed range.** The system always names a crop, even for a field unlike anything it has seen, and the answer will look just as confident.
**Override:** if any reading is outside the survey's recorded range, send the field to Human review.

## 6. Verification

Every push to this repository runs an automated test suite through GitHub Actions. The badge at the top of this page shows the result of the latest run. The tests in [`tests/test_module_integrity.py`](tests/test_module_integrity.py) enforce five publishing rules:

1. No data, notebook or model files (`.db`, `.csv`, `.ipynb`, `.pkl`) exist anywhere in this module.
2. Every figure this manual cites exists in `figures/`.
3. Every figure in `figures/` is cited by this manual.
4. All six required sections are present, in order.
5. The build badge is the first line of the manual.

A green badge proves that these publishing rules held on the latest commit, and nothing more. It does **not** prove that the numbers are correct, that the tier lines are wise, or that the instructions are well written. Those depend on the evidence above and on the people who review it. The figures were regenerated from notebooks 13–15 and the farm survey database in October 2026. Both are deliberately kept out of this repository.
