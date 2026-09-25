# Review sheet: 23 verification failures for author classification

For each case, read the **quotation** and the **source excerpt**, and decide which class applies. Then enter your verdict in `author_review.csv` (column `author_class`, and `author_note` if you disagree or want to add something).

Classes:
- `fabrication`: the quotation contains wording the source does not
- `misquotation`: verbatim words arranged misleadingly (spliced or reordered)
- `from_memory`: accurate text supplied from outside the window
- `unmarked_omission`: verbatim and in order, with running text skipped and no "..."
- `citation_omitted`: verbatim, with an inline citation skipped and no "..."
- `page_furniture`: verbatim, interrupted by a running header, page number or footnote

The "Where the quotation and source diverge" lines show the source text that sits between the matched pieces (SOURCE GAP), and any quoted text not found in order (SPAN-ONLY, marked <<like this>>).

## Case 6: United States v. Clarke

**Question:** On what basis did the Court limit the deference owed to a District Court's discretionary ruling regarding IRS agent examination?

**Quotation (supporting span):**

> First, the District Court's decision is entitled to deference only if based on the correct legal standard. And second, the District Court's latitude does not extend to legal issues about what counts as an illicit motive. they are pure questions of law, so if they arise again on remand, the Court of Appeals has no cause to defer to the District Court.

**Where the quotation and source diverge:**

```
SOURCE GAP (417 ch): '. See Fox v.\nVice, 563 U. S. ___, ___ (2011) (slip op., at 11) (“A trial\ncourt has wide discretion when, but only when, it calls the\ngame by the right rules”). We leave to the Court of Ap-\npeals the task of deciding whether the District Court\nasked and answered the relevant question—once again,\nwhet'
SOURCE GAP (971 ch): '. As\nindicated earlier, one such issue is embedded in the re-\nspondents’ claim that the Government moved to enforce\nthese summonses to gain an unfair advantage in Tax\nCourt litigation. See supra, at 4. The Government re-\nsponds, and the District Court agreed, that any such\n Cite as: 573 U. S. ____ ('
```

**Suggested class:** `unmarked_omission`. Running text and a citation skipped without an ellipsis; all quoted words verbatim and in order.

**Your verdict:** ______________________

## Case 9: Republic of Iraq v. Beaty

**Question:** How did the Court address the effect of the NDAA's subsequent statement that the EWSAA never authorized waiver of federal court jurisdiction?

**Quotation (supporting span):**

> In §1083(d)(1) of the NDAA, the President was given authority to "waive any provision of this section with respect to Iraq." The President proceeded to waive "all" provisions of that section as to Iraq, including (presumably) §1083(c)(4). The Act can therefore add nothing to our analysis of the EWSAA.

**Where the quotation and source diverge:**

```
SOURCE GAP (18 ch): '.” 122 Stat. 343. '
SOURCE GAP (22 ch): '). 73 Fed. Reg. 6571. '
```

**Suggested class:** `citation_omitted`. Inline citations (122 Stat. 343; 73 Fed. Reg. 6571) dropped.

**Your verdict:** ______________________

## Case 14: Fry v. Napoleon Community Schools

**Question:** Why did Congress enact the Handicapped Children's Protection Act of 1986, and what did it accomplish regarding the relationship between IDEA and other disability statutes?

**Quotation (supporting span):**

> Congress was quick to respond. In the Handicapped Children's Protection Act of 1986, 100 Stat. 796, it overturned Smith's preclusion of non-IDEA claims while also adding a carefully defined exhaustion requirement. Now codified at 20 U.S. C. §1415(l), the relevant provision of that statute reads: "Nothing in [the IDEA] shall be construed to restrict or limit the rights, procedures, and remedies available under the Constitution, the [ADA], title V of the Rehabilitation Act [including §504], or other Federal laws protecting the rights of children with disabilities, except that before the filing of a civil action under such laws seeking relief that is also available under [the IDEA], the [IDEA's administrative procedures] shall be exhausted to the same extent as would be required had the action been brought under [the IDEA]."

**Where the quotation and source diverge:**

```
SOURCE GAP (316 ch): '\n\n——————\n 1 At\n the time (and until 1990), the IDEA was called the Education of\nthe Handicapped Act, or EHA. See §901(a), 104 Stat. 1141–1142\n(renaming the statute). To avoid confusion—and acronym overload—\nwe refer throughout this opinion only to the IDEA.\n Cite as: 580 U. S. ____ (2017) 5\n\n Opinio'
SOURCE GAP (12 ch): ' [the IDEA] '
SOURCE GAP (8 ch): ' [ADA], '
SOURCE GAP (19 ch): ' [including §504], '
SOURCE GAP (48 ch): ' IDEA], the [IDEA’s administrative procedures]\n '
```

**Suggested class:** `page_furniture`. Footnote body and page header interrupt the quotation; bracketed alterations in the source.

**Your verdict:** ______________________

## Case 24: Gall v. United States

**Question:** What standard of review should the Court of Appeals have applied, and how did its actual review fall short of that standard?

**Quotation (supporting span):**

> Since the District Court committed no procedural error, the only question for the Court of Appeals was whether the sentence was reasonable—i.e., whether the District Judge abused his discretion in determining that the § 3553(a) factors supported a sentence of probation and justified a substantial deviation from the Guidelines range. The Court of Appeals gave virtually no deference to the District Court's decision that the § 3553(a) factors justified a significant variance in this case. Although the Court of Appeals correctly stated that the appropriate standard of review was abuse of discretion, it engaged in an analysis that more closely resembled de novo review of the facts presented and determined that, in its view, the degree of variance was not warranted.

**Where the quotation and source diverge:**

```
SOURCE GAP (204 ch): ". As we shall now explain, the sentence was reasonable. The Court of Appeals' decision to the contrary was incorrect and failed to demonstrate the requisite deference to the District Judge's decision.\n\nV\n"
```

**Suggested class:** `unmarked_omission`. A sentence of the Court's reasoning skipped without an ellipsis.

**Your verdict:** ______________________

## Case 25: Nichols v. United States

**Question:** What specific actions did Nichols take that led to the federal charges against him?

**Quotation (supporting span):**

> on November 9, 2012, when he abruptly disconnected all of his telephone lines, deposited his apartment keys in his landlord's drop-box, and boarded a flight to Manila

**Where the quotation and source diverge:**

```
SPAN-ONLY: <<on>> November 9, 2012, when he abr
```

**Suggested class:** `fabrication`. One word altered: source "until November 9, 2012", quotation "on November 9, 2012".

**Your verdict:** ______________________

## Case 42: League of United Latin American Citizens v. Perry

**Question:** What factual circumstances prompted the State to redraw District 23, and what specific action did it take in response?

**Quotation (supporting span):**

> Webb County in particular, with a 94% Latino population, spurred the incumbent's near defeat with dramatically increased turnout in 2002. In response to the growing participation that threatened Bonilla's incumbency, the State divided the cohesive Latino community in Webb County, moving about 100,000 Latinos to District 28, which was already a Latino opportunity district, and leaving the rest in a district where they now have little hope of electing their candidate of choice.

**Where the quotation and source diverge:**

```
SOURCE GAP (25 ch): '. See 2004 Almanac 1579. '
```

**Suggested class:** `citation_omitted`. Inline citation (2004 Almanac 1579) dropped.

**Your verdict:** ______________________

## Case 45: League of United Latin American Citizens v. Perry

**Question:** On what basis did the Court reject the argument that African-Americans had effective control of District 24 under the prior plan?

**Quotation (supporting span):**

> Even on the assumption that the first Gingles prong can accommodate this claim, however, appellants must show they constitute 'a sufficiently large minority to elect their candidate of choice with the assistance of cross-over votes.' The District Court found, however, that African-Americans could not elect their candidate of choice in the primary. In support of this finding, it relied on testimony that the district was drawn for an Anglo Democrat, the fact that Frost had no opposition in any of his primary elections since his incumbency began, and District 24's demographic similarity to another district where an African-American candidate failed when he ran against an Anglo.

**Where the quotation and source diverge:**

```
SOURCE GAP (442 ch): '." Voinovich, supra, at 158 (emphasis deleted).\n*444 The relatively small African-American population can meet this standard, according to appellants, because its members constituted 64% of the voters in the Democratic primary. Since a significant number of Anglos and Latinos voted for the Democrat '
```

**Suggested class:** `unmarked_omission`. Citation, star page and two sentences skipped without an ellipsis.

**Your verdict:** ______________________

## Case 61: Credit Suisse Securities (USA) LLC v. Billing

**Question:** On what basis did the Court establish the standard for determining when securities law impliedly precludes antitrust law application?

**Quotation (supporting span):**

> "Repeal of the antitrust laws is to be regarded as implied only if necessary to make the Securities Exchange Act work, and even then only to the minimum extent necessary." And it held that courts should "reconcil[e] the operation of both [i.e., antitrust and securities] statutory schemes ... rather than holding one completely ousted."

**Where the quotation and source diverge:**

```
SOURCE GAP (9 ch): '." Ibid. '
SPAN-ONLY:  necessary." And it held that <<courts should "reconcil[e] the operation of both [i.e., antitrust and securities] statutory schemes ... rather than holding one completely ousted>>."
```

**Suggested class:** `misquotation`. Verbatim words spliced: "And it held that" joined to a quotation the Court introduced with "The Court wrote that, where possible,".

**Your verdict:** ______________________

## Case 67: Gamble v. United States

**Question:** What is the evidentiary foundation of Gamble's argument regarding a bar to prosecution?

**Quotation (supporting span):**

> The foundation of his argument is a decision for which we have no case report: the prosecution in England in 1677 of a man named Hutchinson. Everything for Gamble stems from this one unreported decision.

**Where the quotation and source diverge:**

```
SOURCE GAP (60 ch): '\n Cite as: 587 U. S. ____ (2019) 13\n\n Opinion of the Court\n\n'
SOURCE GAP (332 ch): '. (We have a report of a\ndecision denying Hutchinson bail but no report of his\ntrial.) As told by Gamble, Hutchinson, having been tried\nand acquitted in a foreign court for a murder committed\nabroad, was accused of the same homicide in an English\ntribunal, but the English court held that the foreign'
```

**Suggested class:** `unmarked_omission`. Page header and a parenthetical passage skipped without an ellipsis.

**Your verdict:** ______________________

## Case 77: Boumediene v. Bush

**Question:** What factual differences between post-War Germany and Guantanamo Bay did the Court identify as relevant to the military security analysis?

**Quotation (supporting span):**

> When hostilities in the European Theater came to an end, the United States became responsible for an occupation zone encompassing over 57,000 square miles with a population of 18 million. The United States Naval Station at Guantanamo Bay consists of 45 square miles of land and water.

**Where the quotation and source diverge:**

```
SOURCE GAP (819 ch): '. See Letter from President Truman to Secretary of State Byrnes, (Nov. 28, 1945), in 8 Documents on American Foreign Relations 257 (R. Dennett &amp; R. Turner eds.1948); Pollock, A Territorial Pattern for the Military Occupation of Germany, 38 Am. Pol. Sci. Rev. 970, 975 (1944). In addition to super'
```

**Suggested class:** `unmarked_omission`. Citations and following sentences skipped without an ellipsis.

**Your verdict:** ______________________

## Case 83: Panetti v. Quarterman

**Question:** Why did the Supreme Court conclude that the Court of Appeals' competency standard was constitutionally insufficient?

**Quotation (supporting span):**

> In our view the Court of Appeals' standard is too restrictive to afford a prisoner the protections granted by the Eighth Amendment.... The Court of Appeals concluded that its standard foreclosed petitioner from establishing incompetency by the means he now seeks to employ: a showing that his mental illness obstructs a rational understanding of the State's reason for his execution.

**Where the quotation and source diverge:**

```
SOURCE GAP (1904 ch): ' opinions in Ford, it must be acknowledged, did not set forth a precise standard for competency. The four-Justice plurality discussed the substantive standard at a high level of generality; and Justice Powell wrote only for himself when he articulated more specific criteria. Yet in the portion of Ju'
SPAN-ONLY: ment.... The Court of Appeals <<concluded that its standard foreclosed petitioner from establishing incompetency by the means he now seeks to employ: a showing that his mental illness obstructs a rational understanding of the State's>> reason for his execution.
SOURCE GAP (140 ch): "' standard treats a prisoner's delusional belief system as irrelevant if the prisoner knows that the State has identified his crimes as the "
```

**Suggested class:** `misquotation`. Verbatim sentences joined by an ellipsis in the reverse of their order in the source.

**Your verdict:** ______________________

## Case 86: Panetti v. Quarterman

**Question:** Did Texas law provide Panetti with an opportunity to submit evidence regarding his competency claim?

**Quotation (supporting span):**

> Texas law allows prisoners to submit "affidavits, records, or other evidence supporting the defendant's allegations" "that the defendant is presently incompetent to be executed." Therefore, state law provided Panetti with the legal right to submit whatever evidence he wanted. Here, it is clear that the state court stood ready and willing to consider any evidence Panetti wished to submit.

**Where the quotation and source diverge:**

```
SOURCE GAP (68 ch): 'ex.Code Crim. Proc. Ann., Art. 46.05 (Vernon Supp. Pamphlet 2006). T'
```

**Suggested class:** `citation_omitted`. Statutory citation dropped.

**Your verdict:** ______________________

## Case 87: Panetti v. Quarterman

**Question:** On what basis did the Court reject the argument that Panetti had a constitutional right to specific procedural protections in competency proceedings?

**Quotation (supporting span):**

> Justice Powell's concurrence specifically rejected the Ford plurality's contention that an adversarial proceeding was constitutionally required or even appropriate. This Court has never recognized a right to state-provided experts or counsel on state habeas review. There is likewise no right to transcribed court proceedings, videotaped examinations, or any other specific protocols for conducting competency evaluations.

**Where the quotation and source diverge:**

```
SOURCE GAP (129 ch): ". Part II-B-1, supra. Even a cursory look at Panetti's motions shows that the state court did not err in refusing to grant them. "
SOURCE GAP (411 ch): ". Cf. Ex Parte Motion for Prepayment of Funds to Hire Mental Health Expert to Assist Defense in Article 46.05 Proceedings in Cause No. 3310 (Feb. 19, 2004), 1 App. 54; Defendant's Motion for Appointment of Counsel to Assist Him in Article 46.05 Proceedings (Feb. 19, 2004), id., at 45; Ex Parte Motio"
```

**Suggested class:** `unmarked_omission`. A sentence and a string of record citations skipped without an ellipsis.

**Your verdict:** ______________________

## Case 89: Panetti v. Quarterman

**Question:** How did the Court address the tension between Justice Powell's view and the Ford plurality's position regarding adversarial procedures in competency proceedings?

**Quotation (supporting span):**

> To reach the tenuous conclusion that Justice Powell's opinion constitutes clearly established federal law, the Court ignores the tension between Justice Powell's concern that adversarial proceedings may be counterproductive and the plurality's position that adversarial proceedings are required. Given these contradictory statements, it is difficult to say that Justice Powell's opinion is merely a narrower version of the plurality's view.

**Where the quotation and source diverge:**

```
SOURCE GAP (17 ch): ', ante, at 2856, '
SOURCE GAP (522 ch): '. Compare Ford v. Wainwright, 477 U.S. 399, 426, 106 S.Ct. 2595, 91 L.Ed.2d 335 (1986) (Powell, J., concurring in part and concurring in judgment) (stating that "ordinary adversarial procedures\x97complete with live testimony, cross-examination, and oral argument by counsel\x97are not necessarily the best'
```

**Suggested class:** `citation_omitted`. Citation with explanatory parenthetical dropped.

**Your verdict:** ______________________

## Case 97: Hamdan v. Rumsfeld

**Question:** Why did the Court reject the Government's argument that an effective date provision alone determines whether a statute applies to pre-enactment conduct?

**Quotation (supporting span):**

> a 'statement that a statute will become effective on a certain date does not even arguably suggest that it has any application to conduct that occurred at an earlier date.' INS v. St. Cyr, 533 U. S. 289, 317 (2001)

**Where the quotation and source diverge:**

```
SPAN-ONLY: e.' INS v. St. Cyr, 533 U. S. <<289, 317 (2001>>)
```

**Suggested class:** `from_memory`. Source page break cuts the citation after "533 U. S."; the model completed it correctly ("289, 317 (2001)") from outside the window.

**Your verdict:** ______________________

## Case 102: Hamdan v. Rumsfeld

**Question:** On what basis did the Court reject the Government's argument that the AUMF expanded presidential authority to convene military commissions?

**Quotation (supporting span):**

> there is nothing in the text or legislative history of the AUMF even hinting that Congress intended to expand or alter the authorization set forth in Article 21 of the UCMJ

**Where the quotation and source diverge:**

```
SPAN-ONLY: et forth in Article 21 of the <<UCMJ>>
```

**Suggested class:** `page_furniture`. Footnote interrupts the quoted sentence before "UCMJ".

**Your verdict:** ______________________

## Case 103: Hamdan v. Rumsfeld

**Question:** On what basis did the Court conclude that the AUMF did not expand the President's authority to convene military commissions beyond what Article 21 of the UCMJ permits?

**Quotation (supporting span):**

> there is nothing in the text or legislative history of the AUMF even hinting that Congress intended to expand or alter the authorization set forth in Article 21 of the UCMJ

**Where the quotation and source diverge:**

```
SPAN-ONLY: et forth in Article 21 of the <<UCMJ>>
```

**Suggested class:** `page_furniture`. Footnote interrupts the quoted sentence before "UCMJ".

**Your verdict:** ______________________

## Case 104: Hamdan v. Rumsfeld

**Question:** What three historical circumstances does the Court identify as the contexts in which military commissions have been used?

**Quotation (supporting span):**

> Commissions historically have been used in three situations. First, they have substituted for civilian courts at times and in places where martial law has been declared. Second, commissions have been established to try civilians "as part of a temporary military government over occupied enemy territory or territory regained from an enemy where civil government cannot and does not function." The third type of commission, convened as an "incident to the conduct of war"

**Where the quotation and source diverge:**

```
SOURCE GAP (266 ch): '. See Bradley & Goldsmith, Congressional\nAuthorization and the War on Terrorism, 118 Harv.\nL. Rev. 2048, 2132–2133 (2005); Winthrop 831–846; Hear\nings on H. R. 2498 before the Subcommittee of the House\nCommittee on Armed Services, 81st Cong., 1st Sess., 975\n(1949). '
SOURCE GAP (205 ch): '.\nTheir use in these circumstances has raised constitutional\nquestions, see Duncan v. Kahanamoku, 327 U. S. 304\n(1946); Milligan, 4 Wall., at 121–122, but is well recog\nnized.25 See Winthrop 822, 836–839. '
SOURCE GAP (5 ch): '\nian '
SOURCE GAP (1441 ch): '.” Duncan,\n327 U. S., at 314; see Milligan, 4 Wall., at 141–142 (Chase,\nC. J., concurring in judgment) (distinguishing “MARTIAL\nLAW PROPER” from “MILITARY GOVERNMENT” in occupied\nterritory). Illustrative of this second kind of commission is\n——————\n 25 The justification for, and limitations on, these'
```

**Suggested class:** `unmarked_omission`. Citations, a sentence and a footnote skipped without an ellipsis.

**Your verdict:** ______________________

## Case 106: Hamdan v. Rumsfeld

**Question:** How did the Court distinguish law-of-war commissions from the other two types of military commissions in terms of their jurisdictional scope and purpose?

**Quotation (supporting span):**

> The third type of commission, convened as an "incident to the conduct of war" when there is a need "to seize and subject to disciplinary measures those enemies who in their attempt to thwart or impede our military effort have violated the law of war," Quirin, 317 U. S., at 28–29, has been described as "utterly different" from the other two. Not only is its jurisdiction limited to offenses cognizable during time of war, but its role is primarily a factfinding one—to determine, typically on the battlefield itself, whether the defendant has violated the law of war.

**Where the quotation and source diverge:**

```
SOURCE GAP (149 ch): '.\nBickers, Military Commissions are Constitutionally Sound:\nA Response to Professors Katyal and Tribe, 34 Tex. Tech.\nL. Rev. 899, 902 (2002–2003).27 '
```

**Suggested class:** `citation_omitted`. Law review citation and footnote marker dropped.

**Your verdict:** ______________________

## Case 130: Altria Group, Inc. v. Good

**Question:** How did the Court distinguish the regulations at issue in Reilly from the common-law fraud prohibition in Cipollone?

**Quotation (supporting span):**

> whereas the "prohibition" in Cipollone was the common-law fraud rule, the "prohibitions" in Reilly were the targeted regulations... the challenged regulations targeted advertising that tended to promote tobacco use by children instead of prohibiting false or misleading statements.

**Where the quotation and source diverge:**

```
SPAN-ONLY: eilly were the targeted regula<<tions... the challenged regulations targeted advertising that tended to promote tobacco use by children instead of prohibiting false or misleading statements>>.
```

**Suggested class:** `page_furniture`. Footnote interrupts "regula-tions"; remaining elision marked with an ellipsis.

**Your verdict:** ______________________

## Case 149: Romag Fasteners, Inc. v. Fossil, Inc.

**Question:** Why did the Court reject Fossil's argument that willfulness must be a prerequisite for awarding profits in trademark cases?

**Quotation (supporting span):**

> At the end of it all, the most we can say with certainty is this. Mens rea figured as an important consideration in awarding profits in pre-Lanham Act cases... And the vast majority of the cases both Romag and Fossil cite simply failed to speak clearly to the issue one way or another.

**Where the quotation and source diverge:**

```
SPAN-ONLY: ts in pre-Lanham Act cases... <<And the vast majority of the cases both Romag and Fossil cite simply failed to speak clearly to the issue one way or another>>.
```

**Suggested class:** `page_furniture`. Page header and citations inside an ellipsis the matcher could not align.

**Your verdict:** ______________________

## Case 159: Tapia v. United States

**Question:** How did the Court address the argument that the prohibition on considering rehabilitation applies only to the decision whether to impose imprisonment, not to determining sentence length?

**Quotation (supporting span):**

> Under standard rules of grammar, §3582(a) says: A sentencing judge shall recognize that imprisonment is not appropriate to promote rehabilitation when the court considers the applicable factors of §3553(a)(2); and a court considers these factors when determining

**Where the quotation and source diverge:**

```
SPAN-ONLY:  considers these factors when <<determining>>
```

**Suggested class:** `page_furniture`. Page header falls between "when" and "determining".

**Your verdict:** ______________________

## Case 171: Azar v. Garza

**Question:** On what basis did the Court determine that vacatur was appropriate in this case?

**Quotation (supporting span):**

> Doe's individual claim for injunctive relief—the only claim addressed by the D. C. Circuit—became moot after the abortion. It is undisputed that Garza and her lawyers prevailed in the D. C. Circuit, took voluntary, unilateral action to have Doe undergo an abortion sooner than initially expected, and thus retained the benefit of that favorable judgment. The unique circumstances of this case and the balance of equities weigh in favor of vacatur.

**Where the quotation and source diverge:**

```
SOURCE GAP (32 ch): '-\n4 AZAR v. GARZA\n\n Per Curiam\n\n'
SOURCE GAP (979 ch): '. And although not every moot case will\nwarrant vacatur, the fact that the relevant claim here\nbecame moot before certiorari does not limit this Court’s\ndiscretion. See, e.g., LG Electronics, Inc. v. InterDigital\nCommunications, LLC, 572 U. S. ___ (2014) (after the\ncertiorari petition was filed, res'
```

**Suggested class:** `unmarked_omission`. Page header and a paragraph skipped without an ellipsis.

**Your verdict:** ______________________
