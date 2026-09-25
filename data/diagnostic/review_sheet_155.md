# Review sheet 2: the remaining 155 verification failures

Same procedure as `review_sheet.md`. For each case, check that the quotation matches the source apart from what the "Where the quotation and source diverge" lines show, and decide the class. Enter it in `author_review_155.csv` (column `author_class`; add an `author_note` if you disagree or want to record something).

Classes: `fabrication`, `misquotation`, `from_memory`, `unmarked_omission`, `citation_omitted`, `page_furniture`, `encoding_artefact` (definitions in `review_sheet.md`).

The most common patterns:
- A SOURCE GAP holding "Cite as: …", "Opinion of the Court", a case caption, or a footnote after "——————" is a `page_furniture` case.
- A SOURCE GAP holding "Id., at 12", "See …", or a reporter citation, with the quotation otherwise verbatim, is a `citation_omitted` case.
- A SOURCE GAP holding an invisible control character (the byte 0x9E, shown as a blank or as the escape code backslash-x-9-e) where the quotation has "§" is an `encoding_artefact` case.
- Short SOURCE GAPs such as "[e] " or " [the IDEA] " are editorial brackets in the source, and are not a difference in wording.

## 1/155: case 0, United States v. Clarke

> Congress has granted the Service broad latitude to issue summonses "[f]or the purpose of ascertaining the correctness of any return, making a return where none has been made, determining the liability of any person for any internal revenue tax . . . , or collecting any such liability." §7602(a). Such a summons directs a taxpayer (or associated person) to appear before an IRS official and to provide sworn testimony or produce "books, papers, records, or other data . . . relevant or material to [a tax] inquiry." §7602(a)(1). In that proceeding, we have held, the IRS "need only demonstrate good faith in issuing the summons." United States v. Stuart, 489 U. S. 353, 359 (1989). More specifically, that means establishing what have become known as the Powell factors: "that the investigation will be conducted pursuant to a legitimate purpose, that the inquiry may be relevant to the purpose, that the information sought is not already within the [IRS's] possession, and that the administrative steps required by the [Internal Revenue] Code have been followed."

```
SOURCE GAP (5 ch): '\n“[f]'
SOURCE GAP (3 ch): '1) '
SOURCE GAP (9 ch): ' [a tax] '
SOURCE GAP (129 ch): 'f a taxpayer does not comply with a summons, the IRS\nmay bring an enforcement action in district court. See\n§§7402(b), 7604(a). I'
SOURCE GAP (9 ch): ' [IRS’s]\n'
SOURCE GAP (20 ch): ' [Internal Revenue] '
```

Suggested: `citation_omitted`. Your verdict: ______

## 2/155: case 1, United States v. Clarke

> the respondents asserted that the IRS issued the summonses to "punish[ ] [Dynamo] for refusing to agree to a further extension of the applicable statute of limitations." App. 52. More particularly, they stated in sworn declarations that immediately after Dynamo declined to grant a third extension of time, the IRS, "despite having not asked for additional information for some time, . . . suddenly issued" the summonses. Id., at 95. Second, the respondents averred that the IRS decided to enforce the summonses, subsequent to Dynamo's filing suit in Tax Court, to "evad[e] the Tax Court['s] limitations on discovery"

```
SOURCE GAP (51 ch): '\n4 UNITED STATES v. CLARKE\n\n Opinion of the Court\n\n'
SOURCE GAP (13 ch): '[ ] [Dynamo] '
SPAN-ONLY: uit in Tax Court, to "evad[e] <<the Tax Court>>['s] limitations on discovery"
SOURCE GAP (22 ch): '[e] the Tax Court[’s] '
```

Suggested: `page_furniture`. Your verdict: ______

## 3/155: case 2, United States v. Clarke

> the Court of Appeals cited binding Circuit precedent holding that a simple "allegation of improper purpose," even if lacking any "factual support," entitles a taxpayer to "question IRS officials concerning the Service's reasons for issuing the summons."

```
SOURCE GAP (57 ch): ' as: 573 U. S. ____ (2014) 5\n\n Opinion of the Court\n\ncite'
```

Suggested: `page_furniture`. Your verdict: ______

## 4/155: case 3, United States v. Clarke

> the taxpayer is entitled to examine an IRS agent when he can point to specific facts or circumstances plausibly raising an inference of bad faith. Naked allegations of improper purpose are not enough: The taxpayer must offer some credible evidence supporting his charge. But circumstantial evidence can suffice to meet that burden; after all, direct evidence of another person's bad faith, at this threshold stage, will rarely if ever be available. And although bare assertion or conjecture is not enough, neither is a fleshed out case demanded: The taxpayer need only make a showing of facts that give rise to a plausible inference of improper motive.

```
SOURCE GAP (59 ch): '\n Cite as: 573 U. S. ____ (2014) 7\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 5/155: case 4, United States v. Clarke

> An appellate court, as the Eleventh Circuit noted, reviews for abuse of discretion a trial court's decision to order—or not—the questioning of IRS agents. That standard of review reflects the district court's superior familiarity with, and understanding of, the dispute; and it comports with the way appellate courts review related matters of case management, discovery, and trial practice.

```
SOURCE GAP (111 ch): '. See 517 Fed. Appx., at 691, n. 2; Tiffany Fine\nArts, Inc. v. United States, 469 U. S. 310, 324, n. 7 (1985).\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 6/155: case 5, United States v. Clarke

> An appellate court, as the Eleventh Circuit noted, reviews for abuse of discretion a trial court's decision to order—or not—the questioning of IRS agents. That standard of review reflects the district court's superior familiarity with, and understanding of, the dispute; and it comports with the way appellate courts review related matters of case management, discovery, and trial practice.

```
SOURCE GAP (111 ch): '. See 517 Fed. Appx., at 691, n. 2; Tiffany Fine\nArts, Inc. v. United States, 469 U. S. 310, 324, n. 7 (1985).\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 7/155: case 7, Republic of Iraq v. Beaty

> The last provision was added to the NDAA after the President vetoed an earlier version of the bill, which did not include the waiver authority. The President's veto message said that the bill "would imperil billions of dollars of Iraqi assets at a crucial juncture in that nation's reconstruction efforts." Only when Congress added the waiver authority to the NDAA did the President agree to approve it

```
SOURCE GAP (180 ch): '.” Memorandum to the House of Repre\nsentatives Returning Without Approval the “National\nDefense Authorization Act for Fiscal Year 2008,” 43\nWeekly Comp. of Pres. Doc. 1641 (2007). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 8/155: case 8, Republic of Iraq v. Beaty

> that is an absurd reading, not only textually but in the result it produces: It would mean that the effect of the EWSAA was to permit the President to exclude Iraq from, rather than include it within, such beneficent legislation as the Food for Peace Act of 1966

```
SOURCE GAP (535 ch): '\n\n——————\n 1 The eighth proviso of EWSAA §1503 says that absent further con\n\ngressional action, “the authorities contained in this section shall expire\non September 30, 2004.” 117 Stat. 579. The Court of Appeals ex\npressed doubt that Congress would have wanted federal-court jurisdic\ntion to disappear'
```

Suggested: `page_furniture`. Your verdict: ______

## 9/155: case 10, Republic of Iraq v. Beaty

> As a textual matter, the proffered definition of "inapplicable" is unpersuasive. If a provision of law is "inapplicable" then it cannot be applied; to "apply" a statute is "[t]o put [it] to use." Webster's New International Dictionary 131 (2d ed. 1954). When the District Court exercised jurisdiction over these cases against Iraq, it surely was putting §1605(a)(7) to use with respect to that country. Without the application of that provision, there was no basis for subject-matter jurisdiction. If Congress had wanted to authorize the President merely to cancel Iraq's designation as a state sponsor of terrorism, then Congress could have done so.

```
SPAN-ONLY: ; to "apply" a statute is "[t]<<o pu>>t [it] to use." Webster's New
SOURCE GAP (13 ch): ' “[t]o\nput [i'
SOURCE GAP (60 ch): '\n Cite as: 556 U. S. ____ (2009) 15\n\n Opinion of the Court\n\n'
SOURCE GAP (31 ch): '. 28 U. S. C. §§1604,\n1330(a). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 10/155: case 11, Republic of Iraq v. Beaty

> It is true that the "authorities contained in" §1503 of the EWSAA expired, but expiration of the authorities (viz., the President's powers to suspend and make inapplicable certain laws) is not the same as cancellation of the effect of the President's prior valid exercise of those authorities (viz., the restoration of sovereign immunity). As Iraq points out, Congress has in other statutes provided explicitly that both the authorities granted and the effects of their exercise sunset on a particular date. E.g., 19 U. S. C. §2432(c)(3) ("A waiver with respect to any country shall terminate on the day after the waiver authority granted by this subsection ceases to be effective with respect to such country"). The EWSAA contains no such language.

```
SOURCE GAP (164 ch): '\n——————\n 3 The sunset date was extended by one year in a later bill. 108–106,\n\n§2204(2), 117 Stat. 1230.\n Cite as: 556 U. S. ____ (2009) 17\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 11/155: case 12, Fry v. Napoleon Community Schools

> an "individualized education program," called an IEP for short, serves as the "primary vehicle" for providing each child with the promised FAPE. Crafted by a child's "IEP Team"—a group of school officials, teachers, and parents—the IEP spells out a personalized plan to meet all of the child's "educational needs."

```
SOURCE GAP (131 ch): '.\nHonig v. Doe, 484 U.S. 305, 311 (1988); see §1414(d).\n(Welcome to—and apologies for—the acronymic world of\nfederal legislation.) '
```

Suggested: `citation_omitted`. Your verdict: ______

## 12/155: case 13, Fry v. Napoleon Community Schools

> A regulation implementing Title II requires a public entity to make "reasonable modifications" to its "policies, practices, or procedures" when necessary to avoid such discrimination. 28 CFR §35.130(b)(7) (2016); see, e.g., Alboniga v. School Bd. of Broward Cty., 87 F. Supp. 3d 1319, 1345 (SD Fla. 2015) (requiring an accommodation to permit use of a service animal under Title II). In similar vein, courts have interpreted §504 as demanding certain "reasonable" modifications to existing practices in order to "accommodate" persons with disabilities.

```
SOURCE GAP (62 ch): '\xad\n4 FRY v. NAPOLEON COMMUNITY SCHOOLS\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 13/155: case 15, Fry v. Napoleon Community Schools

> The IDEA, of course, protects only "children" (well, really, adolescents too) and concerns only their schooling... And as earlier noted, the statute's goal is to provide each child with meaningful access to education by offering individualized instruction and related services appropriate to her "unique needs."... By contrast, Title II of the ADA and §504 of the Rehabilitation Act cover people with disabilities of all ages, and do so both inside and outside schools. And those statutes aim to root out disability-based discrimination, enabling each covered person (sometimes by means of reasonable accommodations) to participate equally to all others in public facilities and federally funded programs.

```
SOURCE GAP (60 ch): '\n Cite as: 580 U. S. ____ (2017) 15\n\n Opinion of the Court\n\n'
SOURCE GAP (18 ch): '. §1412(a)(1)(A). '
SOURCE GAP (63 ch): '.”\n§1401(29); see Rowley, 458 U.S., at 192, 198; supra, at 11.\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 14/155: case 16, Fry v. Napoleon Community Schools

> The IDEA, of course, protects only "children" (well, really, adolescents too) and concerns only their schooling. §1412(a)(1)(A). And as earlier noted, the statute's goal is to provide each child with meaningful access to education by offering individualized instruction and related services appropriate to her "unique needs." §1401(29); see Rowley, 458 U.S., at 192, 198; supra, at 11. By contrast, Title II of the ADA and §504 of the Rehabilitation Act cover people with disabilities of all ages, and do so both inside and outside schools. And those statutes aim to root out disability-based discrimination, enabling each covered person (sometimes by means of reasonable accommodations) to participate equally to all others in public facilities and federally funded programs.

```
SOURCE GAP (60 ch): '\n Cite as: 580 U. S. ____ (2017) 15\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 15/155: case 17, Fry v. Napoleon Community Schools

> One clue to whether the gravamen of a complaint against a school concerns the denial of a FAPE, or instead addresses disability-based discrimination, can come from asking a pair of hypothetical questions. First, could the plaintiff have brought essentially the same claim if the alleged conduct had occurred at a public facility that was not a school—say, a public theater or library? And second, could an adult at the school—say, an employee or visitor—have pressed essentially the same grievance? When the answer to those questions is yes, a complaint that does not expressly allege the denial of a FAPE is also unlikely to be truly about that subject; after all, in those other situations there is no FAPE obligation and yet the same basic suit could go forward. But when the answer is no, then the complaint probably does concern a FAPE, even if it does not explicitly say so; for the FAPE requirement is all that explains why only a child in the school setting (not an adult in that setting or a child in some other) has a viable claim.

```
SOURCE GAP (62 ch): '\n16 FRY v. NAPOLEON COMMUNITY SCHOOLS\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 16/155: case 18, Fry v. Napoleon Community Schools

> The Court of Appeals did not undertake the analysis we have just set forward. As noted above, it asked whether E. F.'s injuries were, broadly speaking, 'educational' in nature...That is not the same as asking whether the gravamen of E. F.'s complaint charges, and seeks relief for, the denial of a FAPE. And that difference in standard may have led to a difference in result in this case.

```
SOURCE GAP (257 ch): '. See supra, at 8; 788 F. 3d, at 627 (reasoning that\nthe “value of allowing Wonder to attend [school] with E. F.\nwas educational” because it would foster “her sense of\nindependence and social confidence,” which is “the sort of\ninterest the IDEA protects”). '
SPAN-ONLY:  to a difference in result in <<this case>>.
```

Suggested: `citation_omitted`. Your verdict: ______

## 17/155: case 19, James v. United States

> Whatever weight this legislative history might ordinarily have, we do not find it probative here, because the 1984 enactment on which James relies was not Congress' last word on the subject. In 1986, Congress amended ACCA for the purpose of '`expanding' the range of predicate offenses.' The 1986 amendments added the more expansive language that is at issue in this case... Congress did not consider, much less reject, any such language when it enacted the 1986 amendments.

```
SOURCE GAP (40 ch): 'aylor, supra, at 584, 110 S. Ct. 2143. T'
SOURCE GAP (770 ch): ' \x97 including clause (ii)\'s language defining as violent felonies offenses that are "burglary, arson, extortion, involv[e] use of explosives, or otherwise involv[e] conduct that presents a serious potential risk of physical injury to another." Career Criminals Amendment Act of 1986, § 1402(b), 100 St'
```

Suggested: `citation_omitted`. Your verdict: ______

## 18/155: case 20, James v. United States

> Under this approach, we '`look only to the fact of conviction and the statutory definition of the prior offense,'' and do not generally consider the 'particular facts disclosed by the record of conviction.' That is, we consider whether the elements of the offense are of the type that would justify its inclusion within the residual provision, without inquiring into the specific conduct of this particular offender.

```
SOURCE GAP (141 ch): '." Shepard v. United States, 544 U.S. 13, 17, 125 S. Ct. 1254, 161 L. Ed. 2d 205 (2005) (quoting Taylor, 495 U.S., at 602, 110 S. Ct. 2143). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 19/155: case 21, James v. United States

> But while the statutory language is broad, the Florida Supreme Court has considerably narrowed its application in the context of attempted burglary, requiring an 'overt act directed toward entering or remaining in a structure or conveyance.' Mere preparation is not enough.

```
SOURCE GAP (47 ch): '." Jones v. State, 608 So. 2d 797, 799 (1992). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 20/155: case 22, James v. United States

> We agree that the inclusion of curtilage takes Florida's underlying offense of burglary outside the definition of "generic burglary" set forth in Taylor... But that conclusion is not dispositive, because the Government does not argue that James' conviction for attempted burglary constitutes "burglary" under § 924(e)(2)(B)(ii). Rather, it relies on the residual provision of that clause, which can cover conduct that is outside the strict definition of, but nevertheless similar to, generic burglary.

```
SOURCE GAP (143 ch): ', which requires an unlawful entry into, or remaining in, "a building or other structure." 495 U.S., at 598, 110 S. Ct. 2143 (emphasis added). '
SOURCE GAP (33 ch): ' \x97 as the Court has recognized \x97 '
```

Suggested: `citation_omitted`. Your verdict: ______

## 21/155: case 23, Gall v. United States

> a sentence outside of the Guidelines range must be supported by a justification that '"is proportional to the extent of the difference between the advisory range and the sentence imposed."' Characterizing the difference between a sentence of probation and the bottom of Gall's advisory Guidelines range of 30 months as "extraordinary" because it amounted to "a 100% downward variance," the Court of Appeals held that such a variance must be and here was not supported by extraordinary circumstances.

```
SOURCE GAP (153 ch): '."\'" 446 F.3d 884, 889 (C.A.8 2006) (quoting Claiborne, 439 F.3d, at 481, in turn quoting United States v. Johnson, 427 F.3d 423, 426-427 (C.A.7 2005)). '
SOURCE GAP (21 ch): '," 446 F.3d, at 889, '
```

Suggested: `citation_omitted`. Your verdict: ______

## 22/155: case 26, League of United Latin American Citizens v. Perry

> Appellants contend the new plan is an unconstitutional partisan gerrymander and that the redistricting statewide violates § 2 of the Voting Rights Act of 1965, 79 Stat. 437, as amended, 42 U. S. C. § 1973. Appellants also contend that the use of race and politics in drawing lines of specific districts violates the First Amendment and the Equal Protection Clause of the Fourteenth Amendment.

```
SPAN-ONLY: istricting statewide violates <<§>> 2 of the Voting Rights Act of
SOURCE GAP (3 ch): ' \x9e '
SPAN-ONLY:  437, as amended, 42 U. S. C. <<§>> 1973. Appellants also contend
SOURCE GAP (4 ch): '. \x9e '
```

Suggested: `encoding_artefact`. Your verdict: ______

## 23/155: case 27, League of United Latin American Citizens v. Perry

> Convened as a three-judge court under 28 U. S. C. § 2284, the court heard appellants' constitutional and statutory challenges to a 2003 enactment of the Texas State Legislature that drew new district lines for the 32 seats Texas holds in the United States House of Representatives. This Court vacated that decision and remanded for consideration in light of Vieth v. Jubelirer, 541 U. S. 267 (2004).

```
SPAN-ONLY: judge court under 28 U. S. C. <<§>> 2284, the court heard appella
SOURCE GAP (4 ch): '. \x9e '
SOURCE GAP (287 ch): 'ough appellants do not join each other as to all claims, for the sake of convenience we refer to appellants collectively.) In 2004 the court entered judgment for appellees and issued detailed findings of fact and conclusions of law. Session v. Perry, 298 F. Supp. 2d 451 (per curiam). Th'
```

Suggested: `citation_omitted`. Your verdict: ______

## 24/155: case 28, League of United Latin American Citizens v. Perry

> After the 2002 election, it became apparent that District 23 as then drawn had an increasingly powerful Latino population that threatened to oust the incumbent Republican, Henry Bonilla. Before the 2003 redistricting, the Latino share of the citizen voting-age population was 57.5%, and Bonilla's support among Latinos had dropped with each successive election since 1996. In 2002, Bonilla captured only 8% of the Latino vote, and 51.5% of the overall vote. Faced with this loss of voter support, the legislature acted to protect Bonilla's incumbency by changing the lines—and hence the population mix—of the district.

```
SOURCE GAP (40 ch): '. Session, 298 F. Supp. 2d, at 488-489. '
SOURCE GAP (14 ch): ', *424 ibid., '
SOURCE GAP (3 ch): 'ÔÇö'
SOURCE GAP (3 ch): 'ÔÇö'
```

Suggested: `citation_omitted`. Your verdict: ______

## 25/155: case 29, League of United Latin American Citizens v. Perry

> Webb County, which is 94% Latino, had previously rested entirely within District 23; under the new plan, nearly 100,000 people were shifted into neighboring District 28. The rest of the county, approximately 93,000 people, remained in District 23. To replace the numbers District 23 lost, the State added voters in counties comprising a largely Anglo, Republican area in central Texas. In the newly drawn district, the Latino share of the citizen voting-age population dropped to 46%.

```
SOURCE GAP (15 ch): '. Id., at 489. '
SOURCE GAP (13 ch): 'd., at 488. I'
```

Suggested: `citation_omitted`. Your verdict: ______

## 26/155: case 30, League of United Latin American Citizens v. Perry

> The Court has identified three threshold conditions for establishing a § 2 violation: (1) the racial group is '"sufficiently large and geographically compact to constitute a majority in a single-member district"'; (2) the racial group is '"politically cohesive"'; and (3) the majority '"vot[es] sufficiently as a bloc to enable it . . . usually to defeat the minority's preferred candidate."' These are the so-called Gingles requirements.

```
SPAN-ONLY: conditions for establishing a <<§>> 2 violation: (1) the racial g
SOURCE GAP (3 ch): ' \x9e '
SOURCE GAP (5 ch): '[es] '
SOURCE GAP (161 ch): '."\'" Johnson v. De Grandy, 512 U. S. 997, 1006-1007 (1994) (quoting Growe, 507 U. S., at 40 (in turn quoting Thornburg v. Gingles, 478 U. S. 30, 50-51 (1986))). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 27/155: case 31, League of United Latin American Citizens v. Perry

> The Court has identified three threshold conditions for establishing a § 2 violation: (1) the racial group is "`"sufficiently large and geographically compact to constitute a majority in a single-member district"'"; (2) the racial group is "`"politically cohesive"'"; and (3) the majority "`"vot[es] sufficiently as a bloc to enable it . . . usually to defeat the minority's preferred candidate."'"

```
SPAN-ONLY: conditions for establishing a <<§>> 2 violation: (1) the racial g
SOURCE GAP (3 ch): ' \x9e '
SOURCE GAP (5 ch): '[es] '
```

Suggested: `encoding_artefact`. Your verdict: ______

## 28/155: case 32, League of United Latin American Citizens v. Perry

> The District Court found "racially polarized voting" in south and west Texas, and indeed "throughout the State." The polarization in District 23 was especially severe: 92% of Latinos voted against Bonilla in 2002, while 88% of non-Latinos voted for him. Furthermore, the projected results in new District 23 show that the Anglo citizen voting-age majority will often, if not always, prevent Latinos from electing the candidate of their choice in the district.

```
SOURCE GAP (31 ch): '." Session, supra, at 492-493. '
SOURCE GAP (166 ch): '. App. 134, Table 20 (expert Report of Allan J. Lichtman on Voting-Rights Issues in Texas Congressional Redistricting (Nov. 14, 2003) (hereinafter Lichtman Report)). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 29/155: case 33, League of United Latin American Citizens v. Perry

> While the District Court stated that District 23 had not been an effective opportunity district under Plan 1151C, it recognized the district was "moving in that direction." Indeed, by 2002 the Latino candidate of choice in District 23 won the majority of the district's votes in 13 out of 15 elections for statewide officeholders. And in the congressional race, Bonilla could not have prevailed without some Latino support, limited though it was. State legislators changed District 23 specifically because they worried that Latinos would vote Bonilla out of office.

```
SOURCE GAP (37 ch): '." Session, 298 F. Supp. 2d, at 489. '
SOURCE GAP (69 ch): '. Id., at 518 (Ward, J., concurring in part and dissenting in part). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 30/155: case 34, League of United Latin American Citizens v. Perry

> The circumstance that a group does not win elections does not resolve the issue of vote dilution. We have said that "the ultimate right of § 2 is equality of opportunity, not a guarantee of electoral success for minority-preferred candidates of whatever race."

```
SPAN-ONLY: d that "the ultimate right of <<§>> 2 is equality of opportunity,
SOURCE GAP (3 ch): ' \x9e '
```

Suggested: `encoding_artefact`. Your verdict: ______

## 31/155: case 35, League of United Latin American Citizens v. Perry

> The Court has rejected the premise that a State can always make up for the less-than-equal opportunity of some individuals by providing greater opportunity to others. As set out below, these conflicting concerns are resolved by allowing the State to use one majority-minority district to compensate for the absence of another only when the racial group in each area had a § 2 right and both could not be accommodated.

```
SOURCE GAP (164 ch): '. See id., at 917 ("The vote-dilution injuries suffered by these persons are not remedied by creating a safe majority-black district somewhere else in the State"). '
SPAN-ONLY: cial group in each area had a <<§>> 2 right and both could not be
SOURCE GAP (3 ch): ' \x9e '
```

Suggested: `citation_omitted`. Your verdict: ______

## 32/155: case 36, League of United Latin American Citizens v. Perry

> the State's creation of an opportunity district for those without a § 2 right offers no excuse for its failure to provide an opportunity district for those with a § 2 right. And since there is no § 2 right to a district that is not reasonably compact, the creation of a noncompact district does not compensate for the dismantling of a compact opportunity district

```
SPAN-ONLY:  district for those without a <<§>> 2 right offers no excuse for
SOURCE GAP (3 ch): ' \x9e '
SPAN-ONLY: ity district for those with a <<§>> 2 right. And since there is n
SOURCE GAP (3 ch): ' \x9e '
SPAN-ONLY:  right. And since there is no <<§>> 2 right to a district that is
SOURCE GAP (3 ch): ' \x9e '
SOURCE GAP (35 ch): ', see Abrams, 521 U. S., at 91-92, '
```

Suggested: `citation_omitted`. Your verdict: ______

## 33/155: case 37, League of United Latin American Citizens v. Perry

> THE CHIEF JUSTICE's approach has the deficiency of creating a one-way rule whereby plaintiffs must show compactness but States need not (except, it seems, when using § 2 as a defense to an equal protection challenge)

```
SPAN-ONLY: (except, it seems, when using <<§>> 2 as a defense to an equal pr
SOURCE GAP (3 ch): ' \x9e '
```

Suggested: `encoding_artefact`. Your verdict: ______

## 34/155: case 38, League of United Latin American Citizens v. Perry

> The District Court's general finding of effectiveness cannot substitute for the lack of a finding on compactness, particularly because the District Court measured effectiveness simply by aggregating the voting strength of the two groups of Latinos. Under the District Court's approach, a district would satisfy § 2 no matter how noncompact it was, so long as all the members of a racial group, added together, could control election outcomes.

```
SOURCE GAP (19 ch): '. Id., at 503-504. '
SPAN-ONLY: ach, a district would satisfy <<§>> 2 no matter how noncompact it
SOURCE GAP (3 ch): ' \x9e '
```

Suggested: `citation_omitted`. Your verdict: ______

## 35/155: case 39, League of United Latin American Citizens v. Perry

> In the equal protection context, compactness focuses on the contours of district lines to determine whether race was the predominant factor in drawing those lines. Under § 2, by contrast, the injury is vote dilution, so the compactness inquiry embraces different considerations.

```
SPAN-ONLY: actor in drawing those lines. <<Under §>> 2, by contrast, the injury is
SOURCE GAP (64 ch): '. See Miller v. Johnson, 515 U. S. 900, 916-917 (1995). Under \x9e '
```

Suggested: `citation_omitted`. Your verdict: ______

## 36/155: case 40, League of United Latin American Citizens v. Perry

> The practical consequence of drawing a district to cover two distant, disparate communities is that one or both groups will be unable to achieve their political goals. Compactness is, therefore, about more than "style points"; it is critical to advancing the ultimate purposes of § 2, ensuring minority groups equal "opportunity . . . to participate in the political process and to elect representatives of their choice."

```
SOURCE GAP (45 ch): '," post, at 494 (opinion of ROBERTS, C. J.); '
SPAN-ONLY: cing the ultimate purposes of <<§>> 2, ensuring minority groups e
SOURCE GAP (3 ch): ' \x9e '
```

Suggested: `citation_omitted`. Your verdict: ______

## 37/155: case 41, League of United Latin American Citizens v. Perry

> District 23's Latino voters were poised to elect their candidate of choice. They were becoming more politically active, with a marked and continuous rise in Spanish-surnamed voter registration. In successive elections Latinos were voting against Bonilla in greater numbers, and in 2002 they almost ousted him. Webb County in particular, with a 94% Latino population, spurred the incumbent's near defeat with dramatically increased turnout in 2002.

```
SOURCE GAP (37 ch): '. See Lichtman Report, App. 142-143. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 38/155: case 43, League of United Latin American Citizens v. Perry

> The State chose to break apart a Latino opportunity district to protect the incumbent congressman from the growing dissatisfaction of the cohesive and politically active Latino community in the district. The State then purported to compensate for this harm by creating an entirely new district that combined two groups of Latinos, hundreds of miles apart, that represent different communities of interest. Under § 2, the State must be held accountable for the effect of these choices in denying equal opportunity to Latino voters.

```
SPAN-ONLY: ommunities of interest. Under <<§>> 2, the State must be held acc
SOURCE GAP (3 ch): ' \x9e '
```

Suggested: `encoding_artefact`. Your verdict: ______

## 39/155: case 44, League of United Latin American Citizens v. Perry

> The districts in south and west Texas will have to be redrawn to remedy the violation in District 23, and we have no cause to pass on the legitimacy of a district that must be changed. District 25, in particular, was formed to compensate for the loss of District 23 as a Latino opportunity district, and there is no reason to believe District 25 will remain in its current form once District 23 is brought into compliance with § 2. We therefore vacate the District Court's judgment as to these claims.

```
SOURCE GAP (94 ch): '. See Session, 298 F. Supp. 2d, at 528 (Ward, J., concurring in part and dissenting in part). '
SPAN-ONLY:  brought into compliance with <<§>> 2. We therefore vacate the Di
SOURCE GAP (3 ch): ' \x9e '
```

Suggested: `citation_omitted`. Your verdict: ______

## 40/155: case 46, Torres v. Texas Department of Public Safety

> Alexander Hamilton described three circumstances where the "plan of the Convention" implied that the States waived their sovereign immunity: "where the Constitution in express terms granted an exclusive authority to the Union; where it granted in one instance an authority to the Union and in another prohibited the States from exercising the like authority; and where it granted an authority to the Union, to which a similar authority in the States would be absolutely and totally contradictory and repugnant."

```
SOURCE GAP (59 ch): '\n Cite as: 597 U. S. ____ (2022) 5\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 41/155: case 47, Torres v. Texas Department of Public Safety

> The Constitution, by design, worked "an entire change in the first principles of the system." The Framers gave Congress direct power over the "formation, direction or support of the NATIONAL FORCES." ... The States ultimately ratified the Constitution knowing that their sovereignty would give way to national military policy. Consistent with that structural understanding, Congress has, since the founding era, directed raising and maintaining the national military, including at the expense of state sovereignty.

```
SOURCE GAP (45 ch): 'ederalist No. 23,\nat 148 (A. Hamilton). The F'
SOURCE GAP (59 ch): '\n Cite as: 597 U. S. ____ (2022) 9\n\n Opinion of the Court\n\n'
SOURCE GAP (427 ch): '.” Ibid. (emphasis in original). So\n“general and indefinite” were these powers vis-à-vis the\nStates that “[o]bjections were made against” them as “sub-\nversive of the state governments,” which retained “no con-\ntrol on congress” under the new arrangement. 3 Story\n§§1176, 1177, at 67. Some state conv'
```

Suggested: `citation_omitted`. Your verdict: ______

## 42/155: case 48, Torres v. Texas Department of Public Safety

> We consequently hold that, as part of the plan of the Convention, the States waived their immunity under Congress' Article I power "[t]o raise and support Armies" and "provide and maintain a Navy."

```
SOURCE GAP (72 ch): '\n12 TORRES v. TEXAS DEPARTMENT OF PUBLIC SAFETY\n\n Opinion of the Court\n\n'
SOURCE GAP (5 ch): ' “[t]'
```

Suggested: `page_furniture`. Your verdict: ______

## 43/155: case 49, Torres v. Texas Department of Public Safety

> But PennEast did not require any such history, as the dissent acknowledges. Again, in PennEast, we considered the inferences that flow from our constitutional structure and asked whether States may, consistent with that structure, claim immunity to frustrate federal objectives.

```
SOURCE GAP (96 ch): '. 594 U. S., at ___ (slip\nop., at 19) (citing Texas, 143 U. S., at 646); see post, at 14,\nn. 6. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 44/155: case 50, United States v. Tinklenberg

> In the Sixth Circuit's view, the nine days during which the three motions were pending were not excludable because the motions did not "actually cause a delay, or the expectation of delay, of trial." 579 F. 3d, at 598. Because these 9 days were sufficient to bring the number of nonexcludable days above 70, the Court of Appeals found a violation of the Act. And given the fact that Tinklenberg had already served his prison sentence, it ordered the District Court to dismiss the indictment with prejudice.

```
SOURCE GAP (59 ch): '\n Cite as: 563 U. S. ____ (2011) 3\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 45/155: case 51, United States v. Tinklenberg

> In our view, however, the statutory exclusion does not contain this kind of causation requirement. Rather, the filing of a pretrial motion falls within this provision irrespective of whether it actually causes, or is expected to cause, delay in starting a trial.

```
SOURCE GAP (56 ch): '\n2 UNITED STATES v. TINKLENBERG\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 46/155: case 52, United States v. Tinklenberg

> a statute that forbids the importation of "wild birds" need not require a court to decide whether a particular parrot is, in fact, wild or domesticated. It may intend to place the entire species within that definition without investigation of the characteristics of an individual specimen

```
SOURCE GAP (56 ch): '\n6 UNITED STATES v. TINKLENBERG\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 47/155: case 53, United States v. Tinklenberg

> subparagraph (D) clarifies that the trial court should measure the period of excludable delay for a pretrial motion "from the filing of the motion through the conclusion of the hearing on, or other prompt disposition of such motion," but nowhere does it mention the date on which the trial begins or was expected to begin. Thus, it is best read to instruct measurement of the time actually consumed by consideration of the pretrial motion.

```
SOURCE GAP (40 ch): '. §3161(h)(1)(D) (2006 ed., Supp. III).\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 48/155: case 54, United States v. Tinklenberg

> Second, we are impressed that during the 37 years since Congress enacted the Speedy Trial Act, every Court of Appeals has considered the question before us now, and every Court of Appeals, implicitly or explicitly, has rejected the interpretation that the Sixth Circuit adopted in this case... This unanimity among the lower courts about the meaning of a statute of great practical administrative importance in the daily working lives of busy trial judges is itself entitled to strong consideration, particularly when those courts have maintained that interpretation consistently over a long a period of time... Third, the Sixth Circuit's interpretation would make the subparagraph (D) exclusion significantly more difficult to administer... Fourth, we are reinforced in our conclusion by the difficulty of squaring the Sixth Circuit's interpretation with this Court's precedent... the Court concluded (as the Court of Appeals had held) that the exclusion "was intended to be automatic."

```
SOURCE GAP (998 ch): '. See United States v. Wilson, 835 F. 2d 1440,\n1443 (CADC 1987) (explicit), abrogated on other grounds\nby Bloate v. United States, 559 U. S. ___ (2010); United\nStates v. Hood, 469 F. 3d 7, 10 (CA1 2006) (explicit);\nUnited States v. Cobb, 697 F. 2d 38, 42 (CA2 1982) (ex\nplicit), abrogated on other gr'
SOURCE GAP (59 ch): '\n Cite as: 563 U. S. ____ (2011) 9\n\n Opinion of the Court\n\n'
SOURCE GAP (84 ch): '. See General Dynamics Land Systems, Inc. v.\nCline, 540 U. S. 581, 593–594 (2004).\n '
SOURCE GAP (2804 ch): '. And in doing so, it would significantly hinder\nthe Speedy Trial Act’s efforts to secure fair and efficient\ncriminal trial proceedings. See Zedner v. United States,\n547 U. S. 489, 497 (2006) (noting that the Act’s exceptions\nprovide “necessary flexibility”); H. R. Rep. No. 93–1508, p.\n15 (1974) (th'
SPAN-ONLY: ith this Court's precedent... <<the Court>> concluded (as the Court of Ap
SOURCE GAP (187 ch): '. In Henderson v. United States, 476\nU. S. 321 (1986), the Court rejected the contention that\nthe exclusion provision for pretrial motions governs only\nreasonable delays. The Court there '
```

Suggested: `citation_omitted`. Your verdict: ______

## 49/155: case 55, United States v. Tinklenberg

> Henderson did not consider whether a trial court must determine whether the pretrial motion actually caused postponement of the trial in each individual case. But the Sixth Circuit's interpretation would nonetheless significantly limit the premise of "automatic application" upon which the case rests.

```
SOURCE GAP (60 ch): '\n Cite as: 563 U. S. ____ (2011) 11\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 50/155: case 56, United States v. Tinklenberg

> Under the common-law rule, weekend days and holidays are included when counting a statutory time period of 10 days unless the statute specifically excludes them. See 74 Am. Jur. 2d, Time §22, p. 589 (2001) (in calculating time periods expressed in statutes, "when the time stipulated must necessarily include one or more Saturdays, Sundays, or holidays, those days will not be excluded, in the absence of an express proviso for their exclusion"). And Congress has tended specifically to exclude weekend days and holidays from statutory time periods of 10 days when it intended that result.

```
SOURCE GAP (57 ch): '\n14 UNITED STATES v. TINKLENBERG\n\n Opinion of the Court\n\n'
SOURCE GAP (226 ch): '”). Many courts have treated statutory time\nperiods this way. See, e.g., Howeisen v. Chapman, 195\nInd. 381, 383–384, 145 N. E. 487, 488 (1924); American\nTobacco Co. v. Strickling, 88 Md. 500, 508–511, 41 A.\n1083, 1086 (1898). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 51/155: case 57, United States v. Tinklenberg

> We disagree with the Sixth Circuit's interpretation of both subparagraph (D) and subparagraph (F), and now hold that its interpretations of those two provisions are mistaken. Nonetheless the conclusions the court drew from those two interpretations in relevant part cancel each other out such that the court's ultimate conclusion that Tinklenberg's trial failed to comply with the Speedy Trial Act's deadline is correct.

```
SOURCE GAP (60 ch): '\n Cite as: 563 U. S. ____ (2011) 15\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 52/155: case 58, United States v. Tinklenberg

> That is true enough, but it sheds no light on the meaning of the word "delay"... There is nothing odd in saying that an interval of excludable time under §3161(h)(1)(D) arises "as a consequence" of a party's having filed a pretrial motion; if no pretrial motion is filed, no delay results

```
SOURCE GAP (59 ch): '.” Cf. Bloate, supra, at ___, n. 9 (slip op., at 8, n. 9).\n'
SOURCE GAP (60 ch): '\n Cite as: 563 U. S. ____ (2011) 5\n\n Opinion of SCALIA, J.\n\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 53/155: case 59, Gonzales v. O Centro Espírita Beneficente União Do Vegetal

> The District Court concluded that the evidence on health risks was "in equipoise," and similarly that the evidence on diversion was "virtually balanced." In the face of such an even showing, the court reasoned that the Government had failed to demonstrate a compelling interest justifying what it acknowledged was a substantial burden on the UDV's sincere religious exercise.

```
SOURCE GAP (20 ch): 'd., at 1262, 1266. I'
```

Suggested: `citation_omitted`. Your verdict: ______

## 54/155: case 60, Gonzales v. O Centro Espírita Beneficente União Do Vegetal

> The Government maintains that such evidentiary equipoise is an insufficient basis for issuing a preliminary injunction against enforcement of the Controlled Substances Act. The Government begins by invoking the well-established principle that the party seeking pretrial relief bears the burden of demonstrating a likelihood of success on the merits.

```
SOURCE GAP (230 ch): ". We review the District Court's legal rulings de novo and its ultimate decision to issue the preliminary injunction for abuse of discretion. See McCreary County v. American Civil Liberties Union of Ky., 545 U.S. 844, 867 (2005).\n"
```

Suggested: `citation_omitted`. Your verdict: ______

## 55/155: case 62, Credit Suisse Securities (USA) LLC v. Billing

> The United States advanced the same argument in Gordon. See Brief for United States as Amicus Curiae in Gordon v. New York Stock Exchange, Inc., O.T.1974, No. 74-304, pp. 8, 42. And the Court, in finding immunity, necessarily rejected it. See also NASD, supra, at 694, 95 S. Ct. 2427 (same holding); Herman & MacLean v. Huddleston, 459 U.S. 375, 383, 103 S. Ct. 683, 74 L. Ed. 2d 548 (1983) (finding saving clause applicable to overlap between securities laws where that "overlap [was] neither unusual nor unfortunate"

```
SOURCE GAP (7 ch): ' &amp; '
SOURCE GAP (7 ch): ' [was] '
```

Suggested: `encoding_artefact`. Your verdict: ______

## 56/155: case 63, Gamble v. United States

> "[T]he language of the Clause . . . protects individuals from being twice put in jeopardy 'for the same offence,' not for the same conduct or actions," and "an 'offence' is defined by a law, and each law is defined by a sovereign. So where there are two sovereigns, there are two laws, and two 'offences.'"

```
SPAN-ONLY: the same conduct or actions," <<and>> "an 'offence' is defined by a
SOURCE GAP (935 ch): ',”\nGrady v. Corbin, 495 U.S. 508, 529 (1990), as Justice\nScalia wrote in a soon-vindicated dissent, see United\nStates v. Dixon, 509 U.S. 688 (1993) (overruling Grady).\nAnd the term “ ‘[o]ffence’ was commonly understood in\n1791 to mean ‘transgression,’ that is, ‘the Violation or\nBreaking of a Law.’ ”'
```

Suggested: `page_furniture`. Your verdict: ______

## 57/155: case 64, Gamble v. United States

> A close look at them reveals how fidelity to the Double Jeopardy Clause's text does more than honor the formal difference between two distinct criminal codes. It honors the substantive differences between the interests that two sovereigns can have in punishing the same act.

```
SOURCE GAP (51 ch): '\n6 GAMBLE v. UNITED STATES\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 58/155: case 65, Gamble v. United States

> An assault on a United States marshal, we said, would offend against the Nation and a State: the first by "hindering" the "execution of legal process," and the second by "breach[ing]" the "peace of the State." Ibid. That duality of harm explains how "one act" could constitute "two offences, for each of which [the offender] is justly punishable."

```
SOURCE GAP (59 ch): '\n Cite as: 587 U. S. ____ (2019) 7\n\n Opinion of the Court\n\n'
SOURCE GAP (7 ch): '[ing]” '
SOURCE GAP (16 ch): ' [the offender] '
```

Suggested: `page_furniture`. Your verdict: ______

## 59/155: case 66, Gamble v. United States

> But even in constitutional cases, a departure from precedent 'demands special justification.' Arizona v. Rumsey, 467 U.S. 203, 212 (1984). This means that something more than 'ambiguous historical evidence' is required before we will 'flatly overrule a number of major decisions of this Court.' Welch v. Texas Dept. of Highways and Public Transp., 483 U.S. 468, 479 (1987). And the strength of the case for adhering to such decisions grows in proportion to their 'antiquity.' Montejo v. Louisiana, 556 U.S. 778, 792 (2009). Here, as noted, Gamble's historical arguments must overcome numerous 'major decisions of this Court' spanning 170 years. In light of these factors, Gamble's historical evidence must, at a minimum, be better than middling.

```
SOURCE GAP (53 ch): ',\n12 GAMBLE v. UNITED STATES\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 60/155: case 68, Gamble v. United States

> First, they appear in the reports of cases decided in the Court of Chancery more than a half century after Hutchinson. Second, both judges cite only one source, and it is of lower authority than their own: namely, an account of Hutchinson given by an interested party (a defendant) in a previous, non-criminal case—an account on which the court in that case did not rely or even comment. Insofar as our two judges seem to add their own details to the Hutchinson saga, we are not told where they obtained this information or whether it reflects mere guesses as to how gaps in the story should be filled in, decades after the fact. Finally, the two judges' accounts are not entirely consistent.

```
SOURCE GAP (406 ch): '\n——————\nesties Realme of Englande and other his Graces [Dominions],” Acte\nconcerning the triall of Treasons 1543–1544, 35 Hen. 8 ch. 2 (1543–\n1544), it applied only to treasons and misprisions of treason—not to\nhomicide, of which Hutchinson was accused.\n 5 See G. Squibb, The High Court of Chivalry 5'
```

Suggested: `page_furniture`. Your verdict: ______

## 61/155: case 69, Gamble v. United States

> This suggests that Hutchinson was spared retrial as a matter of discretion ("merc[y]")—which must be true if the Chancellor was right that foreign judgments were not binding.

```
SOURCE GAP (6 ch): '[y]”)—'
SOURCE GAP (754 ch): '-\n——————\n 74 Blackstone 262.\n 8 This statute authorized commissioners to try certain defendants for\nacts of treason or murder committed “in whatsoever other Shire or\nplace, within the King’s dominions or without.” But “[d]espite the\nwords ‘or without’, contemporary opinion seems not to have regarded'
```

Suggested: `page_furniture`. Your verdict: ______

## 62/155: case 70, Gamble v. United States

> All that the Roche court held was that, as a procedural matter, it made no sense to charge the jury with both pleas at once, because a finding for Roche on the first (prior acquittal) would, if successful, bar consideration of the second (not guilty). But on our key question—whether a plea based on a foreign acquittal could be successful—the Roche court said absolutely nothing; it had no occasion to do so.

```
SOURCE GAP (50 ch): '). Roche, 1\nLeach, at 135, 168 Eng. Rep., at 169. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 63/155: case 71, Gamble v. United States

> Summing up the import of the preratification cases on which Gamble's argument rests, we have the following: (1) not a single reported case in which a foreign acquittal or conviction barred a later prosecution for the same act in either Britain or America; (2) not a single reported decision in which a foreign judgment was held to be binding in a civil case in a court of law; (3) fragmentary and not entirely consistent evidence about a 17th-century case in which a defendant named Hutchinson, having been tried and acquitted for murder someplace in the Iberian Peninsula, is said to have been spared a second trial for this crime on some ground, perhaps out of "merc[y]," not as a matter of right; (4) two cases (one criminal, one in admiralty) in which a party invoked a prior foreign judgment, but the court did not endorse or rest anything on the party's reliance on that judgment; and (5) two Court of Chancery cases actually holding that foreign judgments were not (or not generally) treated as barring trial at common law.

```
SOURCE GAP (144 ch): '\n——————\n 11 This decision is also reported as Beake v. Tirrell, Com. 120, 90 Eng.\n\nRep. 379.\n20 GAMBLE v. UNITED STATES\n\n Opinion of the Court\n\n'
SOURCE GAP (6 ch): '[y],” '
```

Suggested: `page_furniture`. Your verdict: ______

## 64/155: case 72, Gamble v. United States

> The distinction between believing successive prosecutions by separate sovereigns unjust and holding them unlawful appears right on the face of the first state case that Gamble discusses. In State v. Brown, 2 N. C. 100, 101 (1794), the court opined that it would be "against natural justice" for a man who stole a horse in the Ohio Territory to be punished for theft in North Carolina just for having brought the horse to that State. To avoid this result, the Brown court simply construed North Carolina's theft law not to reach the defendant's conduct. But it did so precisely because the defendant otherwise could face two prosecutions for the same act of theft—despite the common-law rule against double jeopardy for the same "offence"—since "the offence against the laws of this State, and the offence against the laws of [the Ohio Territory] are distinct."

```
SOURCE GAP (298 ch): '\n——————\n 13 See, e.g., F. Wharton, A Treatise on the Law of Homicide in the\nUnited States 283 (1855); F. Wharton, A Treatise on the Criminal Law\nof the United States 137 (1846); L. MacNally, The Rules of Evidence on\nPleas of the Crown 428 (1802).\n24 GAMBLE v. UNITED STATES\n\n Opinion of the Court\n\n'
SPAN-ONLY:  laws of [the Ohio Territory] <<are distinct>>."
```

Suggested: `page_furniture`. Your verdict: ______

## 65/155: case 73, Lagos v. United States

> The fraud involved generating false invoices for services that Dry Van Logistics had not actually performed and then borrowing money from GE using the false invoices as collateral.

```
SOURCE GAP (50 ch): '\n2 LAGOS v. UNITED STATES\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 66/155: case 74, Lagos v. United States

> The word "investigation" is directly linked by the word "or" to the word "prosecution," with which it shares the article "the." This suggests that the "investigation[s]" and "prosecution[s]" that the statute refers to are of the same general type. And the word "prosecution" must refer to a government's criminal prosecution, which suggests that the word "investigation" may refer to a government's criminal investigation. A similar line of reasoning suggests that the immediately following reference to "proceedings" also refers to criminal proceedings in particular, rather than to "proceedings" of any sort.

```
SOURCE GAP (5 ch): '[s]” '
SPAN-ONLY: tion[s]" and "prosecution[s]" <<tha>>t the statute refers to are of
SOURCE GAP (56 ch): '[s]” that\n4 LAGOS v. UNITED STATES\n\n Opinion of the Cour'
```

Suggested: `page_furniture`. Your verdict: ______

## 67/155: case 75, Lagos v. United States

> Lost income, child care expenses, and transportation expenses are precisely the kind of expenses that a victim would be likely to incur when he or she (or, for a corporate victim like GE, its employees) misses work and travels to talk to government investigators, to participate in a government criminal investigation, or to testify before a grand jury or attend a criminal trial. At the same time, the statute says nothing about the kinds of expenses a victim would often incur when private investigations, or, say, bankruptcy proceedings are at issue, namely, the costs of hiring private investigators, attorneys, or accountants.

```
SOURCE GAP (59 ch): '\n Cite as: 584 U. S. ____ (2018) 5\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 68/155: case 76, Boumediene v. Bush

> In comparison the procedural protections afforded to the detainees in the CSRT hearings are far more limited, and, we conclude, fall well short of the procedures and adversarial mechanisms that would eliminate the need for habeas corpus review. Although the detainee is assigned a "Personal Representative" to assist him during CSRT proceedings, the Secretary of the Navy's memorandum makes clear that person is not the detainee's lawyer or even his "advocate." The Government's evidence is accorded a presumption of validity. The detainee is allowed to present "reasonably available" evidence, but his ability to rebut the Government's evidence against him is limited by the circumstances of his confinement and his lack of counsel at this stage.

```
SOURCE GAP (59 ch): '." See App. to Pet. for Cert. in No. 06-1196, at 155, 172. '
SOURCE GAP (15 ch): '. Id., at 159. '
SOURCE GAP (15 ch): ', id., at 155, '
```

Suggested: `citation_omitted`. Your verdict: ______

## 69/155: case 78, Panetti v. Quarterman

> "Mr. Panetti deliberately and persistently chose to control and manipulate our interview situation," they claimed. They maintained that petitioner "could answer questions about relevant legal issues ... if he were willing to do so."

```
SOURCE GAP (13 ch): '. 1 App. 75. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 70/155: case 79, Panetti v. Quarterman

> The results it would produce, however, show its flaws. As in Martinez-Villareal, if the State's "interpretation of `second or successive' were correct, the implications for habeas practice would be far reaching and seemingly perverse." A prisoner would be faced with two options: forgo the opportunity to raise a Ford claim in federal court; or raise the claim in a first federal habeas application (which generally must be filed within one year of the relevant state-court ruling), even though it is premature. This counterintuitive approach would add to the burden imposed on courts, applicants, and the States, with no clear advantage to any. We conclude there is another reasonable interpretation of § 2244, one that does not produce these distortions and inefficiencies.

```
SOURCE GAP (37 ch): '." 523 U.S., at 644, 118 S.Ct. 1618. '
SOURCE GAP (378 ch): 'e dilemma would apply not only to prisoners with mental conditions indicative of incompetency but also to those with no early sign of mental illness. All prisoners are at risk of deteriorations in their mental state. As a result, conscientious defense attorneys would be obliged to file unripe (and, '
```

Suggested: `citation_omitted`. Your verdict: ______

## 71/155: case 80, Panetti v. Quarterman

> The phrase "second or successive" is not self-defining. It takes its full meaning from our case law, including decisions predating the enactment of the Antiterrorism and Effective Death Penalty Act of 1996 (AEDPA). The Court has declined to interpret "second or successive" as referring to all § 2254 applications filed second or successively in time, even when the later filings address a state-court judgment already challenged in a prior § 2254 application.

```
SOURCE GAP (222 ch): '), 110 Stat. 1214. See Slack v. McDaniel, 529 U.S. 473, 486, 120 S.Ct. 1595, 146 L.Ed.2d 542 (2000) (citing Martinez-Villareal, supra); see also Felker v. Turpin, 518 U.S. 651, 664, 116 S.Ct. 2333, 135 L.Ed.2d 827 (1996). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 72/155: case 81, Panetti v. Quarterman

> Petitioner was entitled to these protections once he had made a "substantial threshold showing of insanity." He made this showing when he filed his Renewed Motion To Determine Competencya fact disputed by no party, confirmed by the trial court's appointment of mental health experts pursuant to Article 46.05(f), and verified by our independent review of the record. The Renewed Motion included pointed observations made by two experts the day before petitioner's scheduled execution; and it incorporated, through petitioner's first Motion To Determine Competency, references to the extensive evidence of mental dysfunction considered in earlier legal proceedings.

```
SOURCE GAP (32 ch): '." Id., at 426, 106 S.Ct. 2595. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 73/155: case 82, Panetti v. Quarterman

> Ford requires, at a minimum, that a court allow a prisoner's counsel the opportunity to make an adequate response to evidence solicited by the state court. In petitioner's case this meant an opportunity to submit psychiatric evidence as a counterweight to the report filed by the court-appointed experts.

```
SOURCE GAP (45 ch): '. See 477 U.S., at 424, 427, 106 S.Ct. 2595. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 74/155: case 84, Panetti v. Quarterman

> Panetti filed only two exhibits with his Renewed Motion to Determine Competency in the state court. See Scott Panetti's Renewed Motion to Determine Competency to Be Executed in Cause No. 3310 (Gillespie Cty., Tex., 216th Jud. Dist., Feb. *2868 4, 2004) (hereinafter Renewed Motion).[6] The first was a one-page letter from Dr. Cunningham to Panetti's counsel describing his 85-minute "preliminary evaluation" of Panetti. Letter from Mark D. Cunningham, Ph.D., to Michael C. Gross (Feb. 3, 2004), 1 App. 108. Far from containing "pointed observations," ante, at 2856, Dr. Cunningham's letter is unsworn, contains no diagnosis, and does not discuss whether Panetti understood why he was being executed. Ibid. Panetti's other exhibit was a one-page declaration of a law professor who attended Cunningham's 85-minute meeting with Panetti. Declaration of David R. Dow (Feb. 3, 2004), id., at 110. Professor Dow obviously made no medical diagnosis and simply discussed his lay perception of Panetti's mental condition in a cursory manner. Ibid. Panetti's Renewed Motion attached no medical reports or records, no sworn testimony from any medical professional, and no diagnosis of any medical condition.

```
SOURCE GAP (155 ch): '. The Court describes Dow as an "expert," ante, at 2856, but law professors are obviously not experts when it comes to medical or psychological diagnoses.\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 75/155: case 85, Panetti v. Quarterman

> Under the Florida law at issue in Ford, the Governor—not a court—made the final decision as to the condemned prisoner's sanity. The prisoner could not submit any evidence and had no opportunity to be heard.

```
SOURCE GAP (56 ch): '. 477 U.S., at 412, 106 S.Ct. 2595 (plurality opinion). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 76/155: case 88, Panetti v. Quarterman

> But the state court made no such finding and may have proceeded simply in an abundance of caution, perhaps to humor the Federal District Court, which had "stay[ed] the execution [for 60 days to] allow the state court a reasonable period of time to consider the evidence of Panetti's current mental state." In any event, the question today is not whether Panetti met Texas' threshold but whether he met the constitutional one. The Court cannot avoid answering that question by relying on a related state-law determination.

```
SOURCE GAP (5 ch): '[ed] '
SOURCE GAP (18 ch): ' [for 60 days to] '
SOURCE GAP (70 ch): '." Order in Case No. A-04-CA-042-SS (Feb. 4, 2004), p. 3, 1 App. 116. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 77/155: case 90, Fourth Estate Pub. Benefit Corp. v. Wall-Street.com, LLC

> Fourth Estate licensed journalism works to respondent Wall-Street.com, LLC (Wall-Street), a news website. The license agreement required Wall-Street to remove from its website all content produced by Fourth Estate before canceling the agreement. Wall-Street canceled, but continued to display articles produced by Fourth Estate. Fourth Estate sued Wall-Street and its owner, Jerrold Burden, for copyright infringement.

```
SOURCE GAP (84 ch): '\n2 FOURTH ESTATE PUB. BENEFIT CORP. v.\n WALL-STREET.COM, LLC\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 78/155: case 91, Fourth Estate Pub. Benefit Corp. v. Wall-Street.com, LLC

> Because the Register had not yet acted on Fourth Estate's applications, the District Court, on Wall-Street and Burden's motion, dismissed the complaint, and the Eleventh Circuit affirmed. We granted Fourth Estate's petition for certiorari to resolve a division among U. S. Courts of Appeals on when registration occurs in accordance with §411(a).

```
SOURCE GAP (140 ch): '. 856 F. 3d 1338 (2017). Thereafter, the\nRegister of Copyrights refused registration of the articles\nWall-Street had allegedly infringed.3\n '
```

Suggested: `citation_omitted`. Your verdict: ______

## 79/155: case 92, Fourth Estate Pub. Benefit Corp. v. Wall-Street.com, LLC

> Time and again, then, Congress has maintained registration as prerequisite to suit, and rejected proposals that would have eliminated registration or tied it to the copyright claimant's application instead of the Register's action.

```
SOURCE GAP (85 ch): '\n10 FOURTH ESTATE PUB. BENEFIT CORP. v.\n WALL-STREET.COM, LLC\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 80/155: case 93, Hamdan v. Rumsfeld

> the President's authority to establish military commissions extends only to "offenders or offenses triable by military [commission] under the law of war"; that the law of war includes the Geneva Convention (III) Relative to the Treatment of Prisoners of War; that Hamdan is entitled to the full protections of the Third Geneva Convention until adjudged, in compliance with that treaty, not to be a prisoner of war; and that, whether or not Hamdan is properly classified as a prisoner of war, the military commission convened to try him was established in violation of both the UCMJ and Common Article 3 of the Third Geneva Convention because it had the power to convict based on evidence the accused would never see or hear

```
SOURCE GAP (14 ch): '\n[commission] '
SOURCE GAP (28 ch): ',” 344 F. Supp. 2d, at\n158; '
SOURCE GAP (89 ch): ', Aug.\n12, 1949, [1955] 6 U. S. T. 3316, T. I. A. S. No. 3364 (Third\nGeneva Convention); '
```

Suggested: `citation_omitted`. Your verdict: ______

## 81/155: case 94, Hamdan v. Rumsfeld

> Hamdan objects to this theory on both constitutional and statutory grounds. Principal among his constitutional arguments is that the Government's preferred reading raises grave questions about Congress' authority to impinge upon this Court's appellate jurisdiction, particularly in habeas cases. Support for this argument is drawn from Ex parte Yerger, 8 Wall. 85 (1869), in which, having explained that "the denial to this court of appellate jurisdiction" to consider an original writ of habeas corpus would "greatly weaken the efficacy of the writ," id., at 102–103, we held that Congress would not be presumed to have effected such denial absent an unmistakably clear statement to the contrary. Hamdan also suggests that, if the Government's reading is correct, Congress has unconstitutionally suspended the writ of habeas corpus.

```
SOURCE GAP (1064 ch): '. See id., at 104–105; see also Felker\nv. Turpin, 518 U. S. 651 (1996); Durousseau v. United\nStates, 6 Cranch 307, 314 (1810) (opinion for the Court by\nMarshall, C. J.) (The “appellate powers of this court” are\nnot created by statute but are “given by the constitution”);\nUnited States v. Klein, 13 W'
```

Suggested: `page_furniture`. Your verdict: ______

## 82/155: case 95, Hamdan v. Rumsfeld

> If anything, the evidence of deliberate omission is stronger here than it was in Lindh. In Lindh, the provisions to be contrasted had been drafted separately but were later "joined together and . . . considered simultaneously when the language raising the implication was inserted." We observed that Congress' tandem review and approval of the two sets of provisions strengthened the presumption that the relevant omission was deliberate... Here, Congress not only considered the respective temporal reaches of paragraphs (1), (2), and (3) of subsection (e) together at every stage, but omitted paragraph (1) from its directive that paragraphs (2) and (3) apply to pending cases only after having rejected earlier proposed versions of the statute that would have included what is now paragraph (1) within the scope of that directive.

```
SOURCE GAP (16 ch): '.” Id., at 330. '
SOURCE GAP (257 ch): '. Id., at 331; see also Field v. Mans, 516 U. S.\n59, 75 (1995) (“The more apparently deliberate the con\ntrast, the stronger the inference, as applied, for example,\nto contrasting statutory sections originally enacted simul\ntaneously in relevant respects”). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 83/155: case 96, Hamdan v. Rumsfeld

> That paragraph (1), along with paragraphs (2) and (3), is to "take effect on the date of enactment," DTA §1005(h)(1), 119 Stat. 2743, is not dispositive; "a 'statement that a statute will become effective on a certain date does not even arguably suggest that it has any application to conduct that occurred at an earlier date.'" Congress deemed that provision insufficient, standing alone, to render subsections (e)(2) and (e)(3) applicable to pending cases; hence its adoption of subsection (h)(2).

```
SOURCE GAP (475 ch): '.’ ” INS v. St. Cyr, 533 U. S.\n Cite as: 548 U. S. ____ (2006) 15\n\n Opinion of the Court\n\nthat would have achieved the result the Government urges\nhere weighs heavily against the Government’s interpreta\ntion. See Doe v. Chao, 540 U. S. 614, 621–623 (2004).10\n——————\n289, 317 (2001) (quoting Landgraf '
```

Suggested: `page_furniture`. Your verdict: ______

## 84/155: case 98, Hamdan v. Rumsfeld

> subsections (e)(2) and (e)(3) "confer" jurisdiction in a manner that cannot conceivably give rise to retroactivity questions under our precedents. The provisions impose no additional liability or obligation on any private party or even on the United States, unless one counts the burden of litigating an appeal—a burden not a single one of our cases suggests triggers retroactivity concerns.

```
SOURCE GAP (1060 ch): '\n\n——————\nDismiss 16–17, n. 12 (“While the DTA does not expressly call for\nSupreme Court review of the District of Columbia Circuit’s decisions,\nSection 1005(e)(2) and (3) . . . do not remove this Court’s jurisdiction\nover such decisions under 28 U. S. C. §1254(1)”).\n 12 This assertion is itself high'
```

Suggested: `page_furniture`. Your verdict: ______

## 85/155: case 99, Hamdan v. Rumsfeld

> Councilman identifies two considerations of comity that together favor abstention pending completion of ongoing court-martial proceedings against service personnel. First, military discipline and, therefore, the efficient operation of the Armed Forces are best served if the military justice system acts without regular interference from civilian courts. Second, federal courts should respect the balance that Congress struck between military preparedness and fairness to individual

```
SOURCE GAP (114 ch): '. See\nNew v. Cohen, 129 F. 3d 639, 643 (CADC 1997); see also\n415 F. 3d, at 36–37 (discussing Councilman and New).\n'
SOURCE GAP (35 ch): 'e Councilman, 420 U. S., at 752. Se'
```

Suggested: `citation_omitted`. Your verdict: ______

## 86/155: case 100, Hamdan v. Rumsfeld

> First, military discipline and, therefore, the efficient operation of the Armed Forces are best served if the military justice system acts without regular interference from civilian courts. See Councilman, 420 U. S., at 752. Second, federal courts should respect the balance that Congress struck between military preparedness and fairness to individual service members when it created "an integrated system of military courts and review procedures, a critical element of which is the Court of Military Appeals, consisting of civilian judges 'completely removed from all military influence or persuasion . . . .'"

```
SOURCE GAP (981 ch): '\n——————\n 16 Councilman distinguished service personnel from civilians, whose\nchallenges to ongoing military proceedings are cognizable in federal\ncourt. See, e.g., United States ex rel. Toth v. Quarles, 350 U. S. 11\n(1955). As we explained in Councilman, abstention is not appropriate\nin cases in whi'
```

Suggested: `page_furniture`. Your verdict: ______

## 87/155: case 101, Hamdan v. Rumsfeld

> the Government has identified no other "important countervailing interest" that would permit federal courts to depart from their general "duty to exercise the jurisdiction that is conferred upon them by Congress." To the contrary, Hamdan and the Government both have a compelling interest in knowing in advance whether Hamdan may be tried by a military commission that arguably is without any basis in law and operates free from many of the procedural rules prescribed by Congress for courts-martial

```
SOURCE GAP (35 ch): '.” Id.,\nat 716 (majority opinion). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 88/155: case 105, Hamdan v. Rumsfeld

> describes at least four preconditions for exercise of jurisdiction by a tribunal of the type convened to try Hamdan. First, "[a] military commission, (except where otherwise authorized by statute), can legally assume jurisdiction only of offenses committed within the field of the command of the convening commander." Winthrop 836. The "field of command" in these circumstances means the "theatre of war." Ibid. Second, the offense charged "must have been committed within the period of the war." Id., at 837. No jurisdiction exists to try offenses "committed either before or after the war." Ibid. Third, a military commission not established pursuant to martial law or an occupation may try only "[i]ndividuals of the enemy's army who have been guilty of illegitimate warfare or other offences in violation of the laws of war" and members of one's own army "who, in time of war, become chargeable with crimes or offences not cognizable, or triable, by the criminal courts or under the Articles of war." Id., at 838. Finally, a law-of-war commission has jurisdiction to try only two kinds of offense: "Violations of the laws and usages of war cognizable by military tribunals only," and "[b]reaches of military orders or regulations for which offenders are not legally triable by court-martial under the Articles of war." Id., at 839.

```
SOURCE GAP (7 ch): ', “[a] '
SOURCE GAP (264 ch): '\n——————\n 28 If the commission is established pursuant to martial law or military\n\ngovernment, its jurisdiction extends to offenses committed within “the\nexercise of military government or martial law.” Winthrop 837.\n34 HAMDAN v. RUMSFELD\n\n Opinion of STEVENS, J.\n\n'
SOURCE GAP (5 ch): ' “[i]'
SOURCE GAP (5 ch): ' “[b]'
```

Suggested: `page_furniture`. Your verdict: ______

## 89/155: case 107, Hamdan v. Rumsfeld

> It is one thing to observe that charges before a military commission 'need not be stated with the precision of a common law indictment,' it is quite another to say that a crime not charged may nonetheless be read into an indictment. Second, the Government plainly had available to it the tools and the time it needed to charge petitioner with the various crimes

```
SOURCE GAP (43 ch): ',’ ” post, at 15, n. 7 (citation omitted); '
```

Suggested: `citation_omitted`. Your verdict: ______

## 90/155: case 108, Hamdan v. Rumsfeld

> At a minimum, the Government must make a substantial showing that the crime for which it seeks to try a defendant by military commission is acknowledged to be an offense against the law of war. That burden is far from satisfied here.

```
SOURCE GAP (959 ch): '\n——————\n 34 While the common law necessarily is “evolutionary in nature,” post,\n\nat 13 (THOMAS, J., dissenting), even in jurisdictions where common law\ncrimes are still part of the penal framework, an act does not become a\ncrime without its foundations having been firmly established in prece\ndent. S'
```

Suggested: `page_furniture`. Your verdict: ______

## 91/155: case 109, Hamdan v. Rumsfeld

> Winthrop's conspiracy "of the first and second classes combined" is, like Howland's example, best understood as a species of compound offense of the type tried by the hybrid military commissions of the Civil War. It is not a stand-alone offense against the law of war.

```
SPAN-ONLY: <<Winthrop>>'s conspiracy "of the first an
SOURCE GAP (1400 ch): ' any\nkind from his own list of offenses against the law of war.\nSee Winthrop 839–840.\n Winthrop does, unsurprisingly, include “criminal con\nspiracies” in his list of “[c]rimes and statutory offenses\ncognizable by State or U. S. courts” and triable by martial\nlaw or military government commission. Se'
```

Suggested: `page_furniture`. Your verdict: ______

## 92/155: case 110, Hamdan v. Rumsfeld

> First, because Hamdan apparently is not subject to the death penalty (at least as matters now stand) and may receive a sentence shorter than 10 years' imprisonment, he has no automatic right to review of the commission's "final decision" before a federal court under the DTA. See §1005(e)(3), 119 Stat. 2743. Second, contrary to the Government's assertion, there is a "basis to presume" that the procedures employed during Hamdan's trial will violate the law: The procedures are described with particularity in Commission Order No. 1, and implementation of some of them has already occurred.

```
SOURCE GAP (60 ch): '\n Cite as: 548 U. S. ____ (2006) 53\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 93/155: case 111, Hamdan v. Rumsfeld

> At least partially in response to subsequent criticism of General Yamashita's trial, the UCMJ's codification of the Articles of War after World War II expanded the category of persons subject thereto to include defendants in Yamashita's (and Hamdan's) position, and the Third Geneva Convention of 1949 extended prisoner-of-war protections to individuals tried for crimes committed before their capture. See 3 Int'l Comm. of Red Cross, Commentary: Geneva Convention Relative to the Treatment of Prisoners of War 413 (1960) (hereinafter GCIII Commentary) (explaining that Article 85, which extends the Convention's protections to "[p]risoners of war prosecuted under the laws of the Detaining Power for acts committed prior to capture," was adopted in response to judicial interpretations of the 1929 Convention, including this Court's decision in Yamashita). The most notorious exception to the principle of uniformity, then, has been stripped of its precedential value.

```
SOURCE GAP (789 ch): '\n——————\n 46 The dissenters’ views are summarized in the following passage:\n “It is outside our basic scheme to condemn men without giving\nreasonable opportunity for preparing defense; in capital or other\nserious crimes to convict on ‘official documents . . .; affidavits; . . .\ndocuments or translati'
SOURCE GAP (5 ch): ' “[p]'
```

Suggested: `page_furniture`. Your verdict: ______

## 94/155: case 112, Hamdan v. Rumsfeld

> Among the inconsistencies Hamdan identifies is that between §6 of the Commission Order, which permits exclusion of the accused from proceedings and denial of his access to evidence in certain circumstances, and the UCMJ's requirement that "[a]ll . . . proceedings" other than votes and deliberations by courts-martial "shall be made a part of the record and shall be in the presence of the accused."

```
SOURCE GAP (5 ch): ' “[a]'
SOURCE GAP (47 ch): '\n58 HAMDAN v. RUMSFELD\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 95/155: case 113, Hamdan v. Rumsfeld

> Assuming arguendo that the reasons articulated in the President's Article 36(a) determination ought to be considered in evaluating the impracticability of applying court-martial rules, the only reason offered in support of that determination is the danger posed by international terrorism. Without for one moment underestimating that danger, it is not evident to us why it should require, in the case of Hamdan's trial, any variance from the rules that govern courts-martial.

```
SOURCE GAP (1221 ch): '\n——————\n 51 We may assume that such a determination would be entitled to a\nmeasure of deference. For the reasons given by JUSTICE KENNEDY, see\npost, at 5 (opinion concurring in part), however, the level of deference\naccorded to a determination made under subsection (b) presum\nably would not be as hi'
```

Suggested: `page_furniture`. Your verdict: ______

## 96/155: case 114, Hamdan v. Rumsfeld

> Whatever else might be said about the Eisentrager footnote, it does not control this case. We may assume that "the obvious scheme" of the 1949 Conventions is identical in all relevant respects to that of the 1929 Convention, and even that that scheme would, absent some other provision of law, preclude Hamdan's invocation of the Convention's provisions as an independent source of law binding the Government's actions and furnishing petitioner with any enforceable right. For, regardless of the nature of the rights conferred on Hamdan, cf. United States v. Rauscher, 119 U. S. 407 (1886), they are, as the Government does not dispute, part of the law of war. And compliance with the law of war is the condition upon which the authority set forth in Article 21 is granted.

```
SOURCE GAP (591 ch): '\n——————\n 57 But see, e.g., 4 Int’l Comm. of Red Cross, Commentary: Geneva\nConvention Relative to the Protection of Civilian Persons in Time of\nWar 21 (1958) (hereinafter GCIV Commentary) (the 1949 Geneva\nConventions were written “first and foremost to protect individuals,\nand not to serve State inte'
SOURCE GAP (56 ch): '. See\nHamdi, 542 U. S., at 520–521 (plurality opinion). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 97/155: case 115, Hamdan v. Rumsfeld

> We need not decide the merits of this argument because there is at least one provision of the Geneva Conventions that applies here even if the relevant conflict is not one between signatories. Article 3, often referred to as Common Article 3 because, like Article 2, it appears in all four Geneva Conventions, provides that in a "conflict not of an international character occurring in the territory of one of the High Contracting Parties, each Party to the conflict shall be bound to apply, as a minimum," certain provisions protecting "[p]ersons taking no active part in the hostilities, including members of armed forces who have laid down their arms and those placed hors de combat by . . . detention."

```
SOURCE GAP (3 ch): '62 '
SOURCE GAP (5 ch): ' “[p]'
SOURCE GAP (1435 ch): '\n——————\n 60 The President has stated that the conflict with the Taliban is a con\n\nflict to which the Geneva Conventions apply. See White House Memo\nrandum, Humane Treatment of Taliban and al Qaeda Detainees 2\n(Feb. 7, 2002), available at http://www.justicescholars.org/pegc/archive/\nWhite_House/bush_'
```

Suggested: `page_furniture`. Your verdict: ______

## 98/155: case 116, Hamdan v. Rumsfeld

> The regular military courts in our system are the courts-martial established by congressional statutes...At a minimum, a military commission "can be 'regularly constituted' by the standards of our military justice system only if some practical need explains deviations from court-martial practice...no such need has been demonstrated here.

```
SOURCE GAP (358 ch): '\n——————\n 64 Thecommentary’s assumption that the terms “properly constituted”\nand “regularly constituted” are interchangeable is beyond reproach; the\nFrench version of Article 66, which is equally authoritative, uses the\nterm “régulièrement constitués” in place of “properly constituted.”\n70 HAMDAN v.'
SOURCE GAP (44 ch): '.” Post, at 8 (opinion concurring in\npart). '
SOURCE GAP (60 ch): '.” Post, at 10. As we\nhave explained, see Part VI–C, supra, '
```

Suggested: `citation_omitted`. Your verdict: ______

## 99/155: case 117, Hamdan v. Rumsfeld

> Trial by military commission raises separation-of-powers concerns of the highest order. Located within a single branch, these courts carry the risk that offenses will be defined, prosecuted, and adjudicated by executive officials without independent review. Concentration of power puts personal liberty in peril of arbitrary action by officials, an incursion the Constitution's three-part system is designed to avoid.

```
SOURCE GAP (65 ch): 'f. Loving v. United\nStates, 517 U. S. 748, 756–758, 760 (1996). C'
SOURCE GAP (70 ch): '\n Cite as: 548 U. S. ____ (2006) 3\n\n KENNEDY, J., concurring in part\n\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 100/155: case 118, Hamdan v. Rumsfeld

> Although we can assume the President's practicability judgments are entitled to some deference, the Court observes that Congress' choice of language in the uniformity provision of 10 U.S.C. §836(b) contrasts with the language of §836(a). This difference suggests, at the least, a lower degree of deference for §836(b) determinations. The rules for military courts may depart from federal-court rules whenever the President 'considers' conformity impracticable, §836(a); but the statute requires procedural uniformity across different military courts 'insofar as [uniformity is] practicable,' §836(b), not insofar as the President considers it to be so.

```
SOURCE GAP (18 ch): '. Ante, at 59–60. '
SOURCE GAP (17 ch): '\n[uniformity is] '
```

Suggested: `citation_omitted`. Your verdict: ______

## 101/155: case 119, Hamdan v. Rumsfeld

> the term 'practicable' cannot be construed to permit deviations based on mere convenience or expedience. 'Practicable' means 'feasible,' that is, 'possible to practice or perform' or 'capable of being put into practice, done, or accomplished.' Congress' chosen language, then, is best understood to allow the selection of procedures based on logistical constraints, the accommodation of witnesses, the security of the proceedings, and the like.

```
SOURCE GAP (61 ch): '.” Webster’s Third New International Dictionary\n1780 (1961). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 102/155: case 120, Hamdan v. Rumsfeld

> the deviations must be explained by some such practical need. In addition to §836, a second UCMJ provision, 10 U. S. C. §821, requires us to compare the commissions at issue to courts-martial.

```
SOURCE GAP (57 ch): '\n6 HAMDAN v. RUMSFELD\n\n KENNEDY, J., concurring in part\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 103/155: case 121, Hamdan v. Rumsfeld

> The regular military courts in our system are the courts-martial established by congressional statutes. Acts of Congress confer on those courts the jurisdiction to try "any person" subject to war crimes prosecution. 10 U. S. C. §818. As the Court explains, moreover, while special military commissions have been convened in previous armed conflicts—a practice recognized in §821—those military commissions generally have adopted the structure and procedure of courts-martial.

```
SOURCE GAP (70 ch): '\n Cite as: 548 U. S. ____ (2006) 9\n\n KENNEDY, J., concurring in part\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 104/155: case 122, Hamdan v. Rumsfeld

> To begin with, the structure and composition of the military commission deviate from conventional court-martial standards. Although these deviations raise questions about the fairness of the trial, no evident practical need explains them.

```
SOURCE GAP (58 ch): '\n12 HAMDAN v. RUMSFELD\n\n KENNEDY, J., concurring in part\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 105/155: case 123, Hamdan v. Rumsfeld

> While a general court-martial requires, absent a contrary election by the accused, at least five members, R. C. M. 501(a)(1); 10 U. S. C. §816(1) (2000 ed. and Supp. III), the Appointing Authority here is free, as noted earlier, to select as few as three. MCO No. 1, §4(A)(2). This difference may affect the deliberative process and the prosecution's burden of persuasion.

```
SOURCE GAP (71 ch): '\n Cite as: 548 U. S. ____ (2006) 15\n\n KENNEDY, J., concurring in part\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 106/155: case 124, Hamdan v. Rumsfeld

> There should be reluctance, furthermore, to reach unnecessarily the question whether, as the plurality seems to conclude, ante, at 70, Article 75 of Protocol I to the Geneva Conventions is binding law notwithstanding the earlier decision by our Government not to accede to the Protocol. For all these reasons, and without detracting from the importance of the right of presence, I would rely on other deficiencies noted here and in the opinion by the Court—deficiencies that relate to the structure and procedure of the commission and that inevitably will affect the proceedings—as the basis for finding the military commissions lack authorization under 10 U. S. C. §836 and fail to be regularly constituted under Common Article 3 and §821.

```
SOURCE GAP (59 ch): '—\n20 HAMDAN v. RUMSFELD\n\n KENNEDY, J., concurring in part\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 107/155: case 125, Altria Group, Inc. v. Good

> Respondents claim that petitioners fraudulently marketed their cigarettes as being "light" and containing " '[l]owered [t]ar and [n]icotine' " to convey to consumers that they deliver less tar and nicotine and are therefore less harmful than regular cigarettes... petitioners have known at all relevant times that human smokers unconsciously engage in compensatory behaviors not registered by Cambridge Filter Method testing that negate the effect of the tar- and nicotine-reducing features of "light" cigarettes.

```
SPAN-ONLY:  "light" and containing " '[l]<<owered [t]ar and>> [n]icotine' " to convey to co
SOURCE GAP (27 ch): ' “ ‘[l]owered [t]ar and\n[n]'
SOURCE GAP (265 ch): '. App. 28a–29a.\n Respondents acknowledge that testing pursuant to the\nCambridge Filter Method2 indicates that tar and nicotine\nyields of Marlboro Lights and Cambridge Lights are lower\nthan those of regular cigarettes. Id., at 30a. Respondents\nallege, however, that '
SOURCE GAP (1059 ch): '\n——————\n 1 The MUTPA provides, as relevant, that “[u]nfair methods of compe\n\ntition and unfair or deceptive acts or practices in the conduct of any\ntrade or commerce are declared unlawful.” §207. In construing that\nsection, courts are to “be guided by the interpretations given by the\nFederal Trade C'
```

Suggested: `citation_omitted`. Your verdict: ______

## 108/155: case 126, Altria Group, Inc. v. Good

> Petitioners moved for summary judgment on the ground that the Labeling Act, 15 U. S. C. §1334(b), expressly pre-empts respondents' state-law cause of action... The District Court thus concluded that respondents' claim rests on a state-law requirement based on smoking and health of precisely the kind that §1334(b) pre-empts, and it granted summary judgment for petitioners.

```
SOURCE GAP (852 ch): '. Relying on\nour decisions in Cipollone v. Liggett Group, Inc., 505 U. S.\n504 (1992), and Lorillard Tobacco Co. v. Reilly, 533 U. S.\n525 (2001), the District Court concluded that respondents’\nMUTPA claim is pre-empted. The court recast respon\ndents’ claim as a failure-to-warn or warning neutralizati'
SOURCE GAP (54 ch): '\n4 ALTRIA GROUP, INC. v. GOOD\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 109/155: case 127, Altria Group, Inc. v. Good

> The claim charges petitioners with "produc[ing] a product it knew contained hidden risks . . . not apparent or known to the consumer"—a claim that "runs to what [petitioners] actually said about Lights and what [respondents] claim they should have said." ... The District Court thus concluded that respondents' claim rests on a state-law requirement based on smoking and health of precisely the kind that §1334(b) pre-empts

```
SOURCE GAP (6 ch): '[ing] '
SOURCE GAP (15 ch): ' [petitioners] '
SOURCE GAP (15 ch): ' [respondents] '
SOURCE GAP (253 ch): '.” 436 F. Supp. 2d 132, 151 (Me. 2006).\nAnd the difference between what petitioners said and\nwhat respondents would have them say is “ ‘intertwined\nwith the concern about cigarette smoking and health.’ ”\nId., at 153 (quoting Reilly, 533 U. S., at 548). '
SOURCE GAP (54 ch): '\n4 ALTRIA GROUP, INC. v. GOOD\n\n Opinion of the Court\n\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 110/155: case 128, Altria Group, Inc. v. Good

> the court concluded that respondents' claim is in substance a fraud claim that alleges that petitioners falsely represented their cigarettes as "light" or having "lowered tar and nicotine" even though they deliver to smokers the same quantities of those components as do regular cigarettes. "The fact that these alleged misrepresentations were unaccompanied by additional statements in the nature of a warning does not transform the claimed fraud into failure to warn" or warning neutralization.

```
SOURCE GAP (15 ch): '. Id., at 36. “'
```

Suggested: `citation_omitted`. Your verdict: ______

## 111/155: case 129, Altria Group, Inc. v. Good

> fraud claims "rely only on a single, uniform standard: falsity." Although it is clear that fidelity to the Act's purposes does not demand the pre-emption of state fraud rules

```
SOURCE GAP (44 ch): '.” 505 U. S., at 529 (plu\nrality opinion).\n '
```

Suggested: `citation_omitted`. Your verdict: ______

## 112/155: case 131, Altria Group, Inc. v. Good

> he "perceive[d] no principled basis for many of the plurality's asserted distinctions among the common-law claims." Id., at 543. Justice Blackmun wrote that Congress could not have "intended to create such a hodgepodge of allowed and disallowed claims when it amended the pre-emption provision in 1970," and lamented the "difficulty lower courts w[ould] encounter in attempting to implement" the plurality's test.

```
SPAN-ONLY: <<he "perceive>>[d] no principled basis for ma
SOURCE GAP (61 ch): '\n Cite as: 555 U. S. ____ (2008) 5\n\n THOMAS, J., dissenting\n\n'
SOURCE GAP (7 ch): '[ould] '
```

Suggested: `page_furniture`. Your verdict: ______

## 113/155: case 132, Altria Group, Inc. v. Good

> The Court interpreted the statute without reference to the presumption or any perceived need to impose a narrow construction on the provision in order to protect the police power of the States. Rather, the Court simply construed the MDA in accordance with ordinary principles of statutory construction.

```
SOURCE GAP (57 ch): '\n12 ALTRIA GROUP, INC. v. GOOD\n\n THOMAS, J., dissenting\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 114/155: case 133, Altria Group, Inc. v. Good

> the regulations in question in Reilly "derived from a gen­eral deceptive practices statute like the one at issue in this case," they were pre-empted because they "targeted adver­tising that tended to promote tobacco use by children instead of prohibiting false or misleading statements." According to the majority, that legal duty contrasts with the regulations here, as "[t]he MUTPA says nothing about either 'smoking' or 'health.'"

```
SOURCE GAP (13 ch): 'nte, at 12. A'
SPAN-ONLY:  the regulations here, as "[t]<<he MUTPA says>> nothing about either 'smoking
SOURCE GAP (75 ch): ' “[t]he MUTPA says\n16 ALTRIA GROUP, INC. v. GOOD\n\n THOMAS, J., dissenting\n\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 115/155: case 134, Altria Group, Inc. v. Good

> Thus, the "duty" or "rule" involved in a failure-to-warn claim is no more specific to smoking and health than is a common-law fraud claim based on the "duty" or "rule" not to use deceptive or misleading trade practices. Yet only for the latter was the Cipollone plurality content to ignore the context in which the claim is asserted. This shifting level of generality was identified as a logical weakness in the original Cipollone plurality decision by a majority of the Court

```
SOURCE GAP (62 ch): '\n Cite as: 555 U. S. ____ (2008) 17\n\n THOMAS, J., dissenting\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 116/155: case 135, Altria Group, Inc. v. Good

> Applying the proper test—i.e., whether a jury verdict on respondents' claims would "impos[e] an obligation" on the cigarette manufacturer "because of the effect of smoking upon health," Cipollone, supra, at 554 (SCALIA, J., concurring in judgment in part and dissenting in part), respondents' state-law claims are expressly pre-empted by §5(b) of the Labeling Act.

```
SOURCE GAP (4 ch): '[e] '
SOURCE GAP (440 ch): ')\n\n——————\n 5 The United States, in its amicus brief and at oral argument, con\xad\n\nspicuously declined to address express pre-emption or defend the\nCipollone opinion’s reasoning. See Brief for United States as Amicus\nCuriae 14–33. Instead, it addressed only the question of implied pre\xad\nemption, an issu'
```

Suggested: `page_furniture`. Your verdict: ______

## 117/155: case 136, Turner v. Rogers

> In light of differences among state courts (and some federal courts) on the applicability of a "right to counsel" in civil contempt proceedings enforcing child support orders, we granted the writ.

```
SOURCE GAP (59 ch): '\n Cite as: 564 U. S. ____ (2011) 5\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 118/155: case 137, Turner v. Rogers

> the "pre-eminent generalization that emerges from this Court's precedents on an indigent's right to appointed counsel is that such a right has been recognized to exist only where the litigant may lose his physical liberty if he loses the litigation." And the Court then drew from these precedents "the presumption that an indigent litigant has a right to appointed counsel only when, if he loses, he may be deprived of his physical liberty."

```
SOURCE GAP (15 ch): '.” Id., at 25.\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 119/155: case 138, Turner v. Rogers

> the Federal Government believes that "the routine use of contempt for non-payment of child support is likely to be an ineffective strategy," the Government also tells us that "coercive enforcement remedies, such as contempt, have a role to play."

```
SOURCE GAP (60 ch): '\n Cite as: 564 U. S. ____ (2011) 11\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 120/155: case 139, Turner v. Rogers

> Those proceedings more closely resemble debt-collection proceedings. The government is likely to have counsel or some other competent representative. Cf. Johnson v. Zerbst, 304 U. S. 458, 462–463 (1938) ('[T]he average defendant does not have the professional legal skill to protect himself when brought before a tribunal with power to take his life or liberty, wherein the prosecution is presented by experienced and learned counsel'

```
SOURCE GAP (7 ch): ') (“[T]'
SOURCE GAP (45 ch): '\n16 TURNER v. ROGERS\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 121/155: case 140, Turner v. Rogers

> Despite a long history of courts exercising contempt authority, Turner has not identified any evidence that courts appointed counsel in those proceedings. See Mine Workers v. Bagwell, 512 U. S. 821, 831 (1994) (describing courts' traditional assumption of "inherent contempt authority"); see also 4 W. Blackstone, Commentaries on the Laws of England 280–285 (1769) (describing the "summary proceedings" used to adjudicate contempt). Indeed, Turner concedes that contempt proceedings without appointed counsel have the blessing of history.

```
SOURCE GAP (61 ch): '\n Cite as: 564 U. S. ____ (2011) 3\n\n THOMAS, J., dissenting\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 122/155: case 141, Turner v. Rogers

> The majority errs in moving beyond the question that was litigated below, decided by the state courts, petitioned to this Court, and argued by the parties here, to resolve a question raised exclusively in the Federal Government's amicus brief.

```
SOURCE GAP (61 ch): '\n Cite as: 564 U. S. ____ (2011) 9\n\n THOMAS, J., dissenting\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 123/155: case 142, Turner v. Rogers

> That some fathers subject to a child support agreement report little or no income "does not mean they do not have the ability to pay any child support." Rather, many "deadbeat dads" "opt to work in the underground economy" to "shield their earnings from child support enforcement efforts." To avoid attempts to garnish their wages or otherwise enforce the support obligation, "deadbeats" quit their jobs, jump from job to job, become self-employed, work under the table, or engage in illegal activity.

```
SOURCE GAP (221 ch): '.” Dept. of Health and\nHuman Services, H. Sorensen, L. Sousa, & S. Schaner,\nAssessing Child Support Arrears in Nine Large States and\nthe Nation 22 (2007) (prepared by The Urban Institute)\n(hereinafter Assessing Arrears). '
SOURCE GAP (108 ch): '.” Mich. Sup. Ct., Task Force Report: The Under\nground Economy 10 (2010) (hereinafter Underground\nEconomy). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 124/155: case 143, Turner v. Rogers

> Because of the difficulties in collecting payment through traditional enforcement mechanisms, many States also use civil contempt proceedings to coerce "deadbeats" into paying what they owe. The States that use civil contempt with the threat of detention find it a "highly effective" tool for collecting child support when nothing else works.

```
SOURCE GAP (567 ch): '\n——————\n 5 See Deadbeat Parents Punishment Act of 1998, 112 Stat. 618 (refer\nring to parents who “willfully fai[l] to pay a support obligation” as\n“[d]eadbeat [p]arents”).\n 6 In this case, Turner switched between eight different jobs in three\n\nyears, which made wage withholding difficult. App. 12a, '
```

Suggested: `page_furniture`. Your verdict: ______

## 125/155: case 144, Turner v. Rogers

> Whether "deadbeat dads" should be threatened with incarceration is a policy judgment for state and federal lawmakers, as is the entire question of government involvement in the area of child support.

```
SOURCE GAP (60 ch): 'ite as: 564 U. S. ____ (2011) 13\n\n THOMAS, J., dissenting\n\nc'
```

Suggested: `citation_omitted`. Your verdict: ______

## 126/155: case 145, Burton v. Stewart

> But unlike Burton, the prisoner there had attempted to bring this claim in his initial habeas petition, prompting us to look to Lundy in concluding that the claim "should be treated in the same manner as the claim of a petitioner who returns to a federal habeas court after exhausting state remedies," that is, characterizing it as not "second or successive." Indeed, we expressly declined to address the situation where a petitioner fails to raise the claim in the initial petition.

```
SOURCE GAP (57 ch): '." Martinez-Villareal, 523 U.S., at 644, 118 S.Ct. 1618. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 127/155: case 146, Romag Fasteners, Inc. v. Fossil, Inc.

> Romag discovered that the factories Fossil hired in China to make its products were using counterfeit Romag fasteners—and that Fossil was doing little to guard against the practice.

```
SOURCE GAP (65 ch): '\n2 ROMAG FASTENERS, INC. v. FOSSIL, INC.\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 128/155: case 147, Romag Fasteners, Inc. v. Fossil, Inc.

> The Lanham Act speaks often and expressly about mental states. Section 1117(b) requires courts to treble profits or damages and award attorney's fees when a defendant engages in certain acts intentionally and with specified knowledge. Section 1117(c) increases the cap on statutory damages from $200,000 to $2,000,000 for certain willful violations. Section 1118 permits courts to order the infringing items be destroyed if a plaintiff proves any violation of §1125(a) or a willful violation of §1125(c). Section 1114 makes certain innocent infringers subject only to injunctions. Without doubt, the Lanham Act exhibits considerable care with mens rea standards. The absence of any such standard in the provision before us, thus, seems all the more telling.

```
SOURCE GAP (321 ch): '. Elsewhere, the statute specifies certain\nmens rea standards needed to establish liability, before\neven getting to the question of remedies. See, e.g.,\n§§1125(d)(1)(A)(i), (B)(i) (prohibiting certain conduct only if\nundertaken with “bad faith intent” and listing nine factors\nrelevant to ascertainin'
SOURCE GAP (65 ch): '\n4 ROMAG FASTENERS, INC. v. FOSSIL, INC.\n\n Opinion of the Court\n\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 129/155: case 148, Romag Fasteners, Inc. v. Fossil, Inc.

> A principle is a 'fundamental truth or doctrine, as of law; a comprehensive rule or doctrine which furnishes a basis or origin for others.' And treatises and handbooks on the 'principles of equity' generally contain transsubstantive guidance on broad and fundamental questions about matters like parties, modes of proof, defenses, and remedies... Congress itself has elsewhere used 'equitable principles' in just this way: An amendment to a different section of the Lanham Act lists 'laches, estoppel, and acquiescence' as examples of 'equitable principles.'

```
SOURCE GAP (148 ch): '.”\nBlack’s Law Dictionary 1417 (3d ed. 1933); Black’s Law\n Cite as: 590 U. S. ____ (2020) 5\n\n Opinion of the Court\n\nDictionary 1357 (4th ed. 1951). '
SOURCE GAP (522 ch): '. See, e.g., E. Merwin, Principles of Equity\nand Equity Pleading (1895); J. Indermaur & C. Thwaites,\nManual of the Principles of Equity (7th ed. 1913); H. Smith,\nPractical Exposition of the Principles of Equity (5th ed.\n1914); R. Megarry, Snell’s Principles of Equity (23d ed.\n1947). Our precedent, t'
```

Suggested: `page_furniture`. Your verdict: ______

## 130/155: case 150, House v. Bell

> Lora testified that after leaving Luttrell's house with her mother, she and her brother "went to bed." Later, she heard someone, or perhaps two different people, ask for her mother... "Well, they said that daddy had a wreck down the road and she started cryingnext to the creek." Lora did not describe hearing any struggle.

```
SOURCE GAP (15 ch): '." Id., at 18. '
SOURCE GAP (670 ch): '. Lora\'s account of the events after she went to bed was as follows:\n"Q Laura [sic], at some point after you got back home and you went to bed, did anything happen that caused your mother to be upset or did you hear anything?\n"A Well, it sounded like PawPaw said\x97where\'s daddy at, and she said diggin'
SOURCE GAP (160 ch): '.\n"Q Your mother started crying. What was it that they said?\n"A That daddy had a wreck.\n"Q Did they say where?\n"A Down there next to the creek." Id., at 18-19.\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 131/155: case 151, House v. Bell

> Late in the evening on Monday, July 15two days after the murderlaw enforcement officers visited Turner's trailer. With Turner's consent, Agent Scott seized the pants House was wearing the night Mrs. Muncey disappeared. The heavily soiled pants were sitting in a laundry hamper; years later, Agent Scott recalled noticing "reddish brown stains" he "suspected" were blood. Around 4 p.m. the next day, two local law enforcement officers set out for the Federal Bureau of Investigation in Washington, D. C., with House's pants, blood samples from the autopsy, and other evidence packed together in a box. They arrived at 2 a.m. the next morning. On July 17, after initial FBI testing revealed human blood on the pants, House was arrested.

```
SOURCE GAP (19 ch): '. Id., at 274-275. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 132/155: case 152, House v. Bell

> the habeas court must consider `all the evidence,' old and new, incriminating and exculpatory, without regard to whether it would necessarily be admitted under "rules of admissibility that would govern at trial." Based on this total record, the court must make "a probabilistic determination about what reasonable, properly instructed jurors would do." The court's function is not to make an independent factual determination about what likely occurred, but rather to assess the likely impact of the evidence on reasonable jurors.

```
SOURCE GAP (145 ch): '." See id., at 327-328 (quoting Friendly, Is Innocence Irrelevant? Collateral Attack on Criminal Judgments, 38 U. Chi. L. Rev. 142, 160 (1970)). '
SOURCE GAP (22 ch): '." 513 U. S., at 329. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 133/155: case 153, House v. Bell

> the gateway actual-innocence standard is "by no means equivalent to the standard of Jackson v. Virginia, 443 U. S. 307 (1979)," which governs claims of insufficient evidence. When confronted with a challenge based on trial evidence, courts presume the jury resolved evidentiary disputes reasonably so long as sufficient evidence supports the verdict. Because a Schlup claim involves evidence the trial jury did not have before it, the inquiry requires the federal court to assess how reasonable jurors would react to the overall, newly supplemented record.

```
SOURCE GAP (15 ch): '. Id., at 330. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 134/155: case 154, Tapia v. United States

> The court indicated that Tapia should serve a prison term long enough to qualify for and complete that program: "The sentence has to be sufficient to provide needed correctional treatment, and here I think the needed correctional treatment is the 500 Hour Drug Program. . . . . . "Here I have to say that one of the factors that—I am going to impose a 51-month sentence, . . . and one of the factors that affects this is the need to provide treatment. In other words, so she is in long enough to get the 500 Hour Drug Program, number one."

```
SOURCE GAP (51 ch): '\n2 TAPIA v. UNITED STATES\n\n Opinion of the Court\n\n '
```

Suggested: `page_furniture`. Your verdict: ______

## 135/155: case 155, Tapia v. United States

> We granted certiorari to consider whether §3582(a) permits a sentencing court to impose or lengthen a prison term in order to foster a defendant's rehabilitation. 562 U. S. ___ (2010). That question has divided the Courts of Appeals.

```
SOURCE GAP (60 ch): ')\n Cite as: 564 U. S. ____ (2011) 3\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 136/155: case 156, Tapia v. United States

> Congress accordingly enacted the Sentencing Reform Act of 1984, 98 Stat. 1987 (SRA or Act), to overhaul federal sentencing practices. The Act abandoned indeterminate sentencing and parole in favor of a system in which Sentencing Guidelines, promulgated by a new Sentencing Commission, would provide courts with "a range of determinate sentences for categories of offenses and defendants." And the Act further channeled judges' discretion by establishing a framework to govern their consideration and imposition of sentences.

```
SOURCE GAP (33 ch): '.” Mistretta, 488 U. S., at 368. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 137/155: case 157, Tapia v. United States

> These four considerations—retribution, deterrence, incapacitation, and rehabilitation—are the four purposes of sentencing generally, and a court must fashion a sentence "to achieve the[se] purposes . . . to the extent that they are applicable" in a given case. §3551(a). The SRA then provides additional guidance about how the considerations listed in §3553(a)(2) pertain to each of the Act's main sentencing options—imprisonment, supervised release, probation, and fines. See §3582(a); §3583; §3562(a); §3572(a). These provisions make clear that a particular purpose may apply differently, or even not at all, depending on the kind of sentence under consideration.

```
SOURCE GAP (5 ch): '[se] '
SOURCE GAP (50 ch): '\n6 TAPIA v. UNITED STATES\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 138/155: case 158, Tapia v. United States

> A judge who "perceives clearly" that imprisonment is not an appropriate means of promoting rehabilitation would hardly incarcerate someone for that purpose. Ditto for a judge who "realizes" or "recalls" that imprisonment is not a way to rehabilitate an offender. To be sure, the drafters of the "recognizing" clause could have used still more commanding language: Congress could have inserted a "thou shalt not" or equivalent phrase to convey that a sentencing judge may never, ever, under any circumstances consider rehabilitation in imposing a prison term. But when we interpret a statute, we cannot allow the perfect to be the enemy of the merely excellent.

```
SOURCE GAP (51 ch): '\n8 TAPIA v. UNITED STATES\n\n Opinion of the Court\n\n“'
```

Suggested: `page_furniture`. Your verdict: ______

## 139/155: case 160, Tapia v. United States

> Under standard rules of grammar, §3582(a) says: A sentencing judge shall recognize that imprisonment is not appropriate to promote rehabilitation when the court considers the applicable factors of §3553(a)(2); and a court considers these factors when determining both whether to imprison an offender and what length of term to give him. The use of the word "imprisonment" in the "recognizing" clause does not destroy—but instead fits neatly into—this construction. "Imprisonment" as used in the clause most naturally means "[t]he state of being confined" or "a period of confinement."

```
SOURCE GAP (59 ch): '\n Cite as: 564 U. S. ____ (2011) 9\n\n Opinion of the Court\n\n'
SOURCE GAP (5 ch): ' “[t]'
```

Suggested: `page_furniture`. Your verdict: ______

## 140/155: case 161, Tapia v. United States

> decades of experience with indeterminate sentencing, resulting in the release of many inmates after they completed correctional programs, had left Congress skeptical that "rehabilitation can be induced reliably in a prison setting." S. Rep., at 38. Although some critics argued that "rehabilitation should be eliminated completely as a purpose of sentencing," Congress declined to adopt that categorical position. Instead, the Report explains, Congress barred courts from considering rehabilitation in imposing prison terms, ibid., and n. 165, but not in ordering other kinds of sentences, ibid., and n. 164.

```
SOURCE GAP (12 ch): 'd., at 76. I'
```

Suggested: `citation_omitted`. Your verdict: ______

## 141/155: case 162, Sereboff v. Mid Atlantic Medical Services, Inc.

> Mid Atlantic's action to enforce the "Acts of Third Parties" provision qualifies as an equitable remedy because it is indistinguishable from an action to enforce an equitable lien established by agreement, of the sort epitomized by our decision in Barnes. Mid Atlantic need not characterize its claim as a freestanding action for equitable subrogation. Accordingly, the parcel of equitable defenses the Sereboffs claim accompany any such action are beside the point.

```
SOURCE GAP (225 ch): '. See 4 Palmer, Law of Restitution § 23.18(d), at 470 (A subrogation lien "is not an express lien based on agreement, but instead is an equitable lien impressed on moneys on the ground that they ought to go to the insurer"). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 142/155: case 163, Negusie v. Holder

> When petitioner refused to fight against Ethiopia, his other homeland, the Eritrean Government incarcerated him. Prison guards punished petitioner by beating him with sticks and placing him in the hot sun. He was released after two years and forced to work as a prison guard, a duty he performed on a rotating basis for about four years. It is undisputed that the prisoners he guarded were being persecuted on account of a protected ground—i.e., "race, religion, nationality, membership in a particular social group, or political opinion." 8 U. S. C. §1101(a)(42). Petitioner testified that he carried a gun, guarded the gate to prevent escape, and kept prisoners from taking showers and obtaining fresh air. He also guarded prisoners to make sure they stayed in the sun, which he knew was a form of punishment.

```
SOURCE GAP (59 ch): '\n Cite as: 555 U. S. ____ (2009) 3\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 143/155: case 164, Negusie v. Holder

> In denying relief in this case the BIA recited a rule that has developed in its own case law in reliance on Fedorenko: "[A]n alien's motivation and intent are irrelevant to the issue of whether he 'assisted' in persecution . . . [I]t is the objective effect of an alien's actions which is controlling." The rule is based on three earlier decisions: Matter of Laipenieks, 18 I. & N. Dec. 433 (1983); Matter of Fedorenko, 19 I. & N. Dec. 57; and Matter of Rodriguez-Majano, 19 I. & N. Dec. 811 (1988).

```
SOURCE GAP (6 ch): ': “[A]'
SOURCE GAP (10 ch): ' . . . [I]'
SOURCE GAP (30 ch): '.” App. to Pet. for Cert. 6a. '
```

Suggested: `citation_omitted`. Your verdict: ______

## 144/155: case 165, Negusie v. Holder

> Immigration judges already face the overwhelming task of attempting to recreate, by a limited number of witnesses speaking through (often poor-quality) translation, events that took place years ago in foreign, usually impoverished countries. Adding on top of that the burden of adjudicating claims of duress and coercion, which are extremely difficult to corroborate and necessarily pose questions of degree that require intensely fact-bound line-drawing, would increase the already inherently high risk of error. And the cost of error (viz., allowing uncoerced persecutors to remain in the country permanently) might reasonably be viewed by the agency as significantly greater than the cost of overinclusion under a bright-line rule

```
SOURCE GAP (123 ch): '. See Dia v. Ashcroft, 353 F. 3d\n228, 261–262 (CA3 2003) (en banc) (Alito, J., concurring in\npart and dissenting in part). '
SOURCE GAP (47 ch): '\n4 NEGUSIE v. HOLDER\n\n SCALIA, J., concurring\n\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 145/155: case 166, Alleyne v. United States

> He argued that it was clear from the verdict form that the jury did not find brandishing beyond a reasonable doubt and that he was subject only to the 5-year minimum for "us[ing] or carr[ying] a firearm." Alleyne contended that raising his mandatory minimum sentence based on a sentencing judge's finding that he brandished a firearm would violate his Sixth Amendment right to a jury trial.

```
SOURCE GAP (60 ch): '\n Cite as: 570 U. S. ____ (2013) 3\n\n Opinion of THOMAS, J.\n\n'
SPAN-ONLY: e 5-year minimum for "us[ing] <<or carr>>[ying] a firearm." Alleyne con
SOURCE GAP (20 ch): '[ing] or carr[ying] '
```

Suggested: `page_furniture`. Your verdict: ______

## 146/155: case 167, Alleyne v. United States

> Any fact that, by law, increases the penalty for a crime is an "element" that must be submitted to the jury and found beyond a reasonable doubt. Mandatory minimum sentences increase the penalty for a crime. It follows, then, that any fact that increases the mandatory minimum is an "element" that must be submitted to the jury.

```
SOURCE GAP (31 ch): '. See id.,\nat 483, n. 10, 490. '
SOURCE GAP (75 ch): '\n2 ALLEYNE v. UNITED STATES\n\n Opinion of THOMAS, J.\n Opinion of the Court\n\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 147/155: case 168, Alleyne v. United States

> Apprendi's definition of "elements" necessarily includes not only facts that increase the ceiling, but also those that increase the floor. Both kinds of facts alter the prescribed range of sentences to which a defendant is exposed and do so in a manner that aggravates the punishment.

```
SOURCE GAP (60 ch): '\n Cite as: 570 U. S. ____ (2013) 7\n\n Opinion of THOMAS, J.\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 148/155: case 169, Alleyne v. United States

> It is indisputable that a fact triggering a mandatory minimum alters the prescribed range of sentences to which a criminal defendant is exposed. But for a finding of brandishing, the penalty is five years to life in prison; with a finding of brandishing, the penalty becomes seven years to life. Just as the maximum of life marks the outer boundary of the range, so seven years marks its floor. And because the legally prescribed range is the penalty affixed to the crime, infra, this page, it follows that a fact increasing either end of the range produces a new penalty and constitutes an ingredient of the offense.

```
SOURCE GAP (86 ch): '. Apprendi, supra,\nat 490; Harris, 536 U. S., at 575, 582 (THOMAS, J., dissent-\ning). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 149/155: case 170, Alleyne v. United States

> Moreover, it is impossible to dispute that facts increasing the legally prescribed floor aggravate the punishment. Elevating the low-end of a sentencing range heightens the loss of liberty associated with the crime: the defendant's "expected punishment has increased as a result of the narrowed range" and "the prosecution is empowered, by invoking the mandatory minimum, to require the judge to impose a higher punishment than he might wish." Why else would Congress link an increased mandatory minimum to a particular aggravating fact other than to heighten the consequences for that behavior?

```
SOURCE GAP (132 ch): '.\nHarris, supra, at 579 (THOMAS, J., dissenting); O’Brien,\n560 U. S., at ___ (THOMAS, J., concurring in judgment)\n(slip op., at 2). '
SOURCE GAP (53 ch): '.” Apprendi, supra, at 522 (THOMAS,\nJ., concurring). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 150/155: case 172, Azar v. Garza

> all attorneys must remain aware of the principle that zealous advocacy does not displace their obligations as officers of the court. Especially in fast-paced, emergency proceedings like those at issue here, it is critical that lawyers and courts alike be able to rely on one another's representations. On the other hand, lawyers also have ethical obligations to their clients and not all communication breakdowns constitute misconduct. The Court need not delve into the factual disputes raised by the parties in order to answer the Munsingwear question here.

```
SOURCE GAP (49 ch): '\n Cite as: 584 U. S. ____ (2018) 5\n\n Per Curiam\n\n'
```

Suggested: `page_furniture`. Your verdict: ______

## 151/155: case 173, Burlington Northern & Santa Fe Railway Co. v. United States

> Despite these improvements, B&B remained a "'[s]loppy' [o]perator." Over the course of B&B's 28 years of operation, delivery spills, equipment failures, and the rinsing of tanks and trucks allowed Nemagon, D–D and dinoseb to seep into the soil and upper levels of ground water of the Arvin facility.

```
SPAN-ONLY: ovements, B&B remained a "'[s]<<loppy' [o]perator>>." Over the course of B&B's 28
SOURCE GAP (76 ch): '\n“ ‘[s]loppy’ [o]perator.” App. to Pet. for Cert. in No. 07–\n1601, p. 130a. '
SOURCE GAP (523 ch): '\n——————\nmerous tank failures and spills as the chemical rusted tanks and\neroded valves.\n 2 F.o.b. destination means “the seller must at his own expense and\n\nrisk transport the goods to [the destination] and there tender delivery\nof them . . . .” U. C. C. §2–319(1)(b) (2001). The District Court found'
```

Suggested: `citation_omitted`. Your verdict: ______

## 152/155: case 174, Burlington Northern & Santa Fe Railway Co. v. United States

> the court stated that Shell could still be held liable under a " 'broader' category of arranger liability" if the "disposal of hazardous wastes [wa]s a foreseeable byproduct of, but not the purpose of, the transaction giving rise to" arranger liability. Relying on CERCLA's definition of "disposal," which covers acts such as "leaking" and "spilling," 42 U. S. C. §6903(3), the Ninth Circuit concluded that an entity could arrange for "disposal"

```
SOURCE GAP (5 ch): '\n[wa]'
SOURCE GAP (8 ch): '. Ibid.\n'
```

Suggested: `citation_omitted`. Your verdict: ______

## 153/155: case 175, Burlington Northern & Santa Fe Railway Co. v. United States

> the District Court found it "indisputable that the overwhelming majority of hazardous substances were released from the B&B parcel." Id., at 248a. The court explained that "the predominant activities conducted on the Railroad parcel through the years were storage and some washing and rinsing of tanks, other receptacles, and chemical application vehicles. Mixing, formulating, loading, and unloading of ag-chemical hazardous substances, which contributed most of the liability causing releases, were predominantly carried out by B&B on the B&B parcel."

```
SOURCE GAP (1675 ch): '\n6 BURLINGTON N. & S. F. R. CO. v. UNITED STATES\n\n Opinion of the Court\n\nproducts, the court held Shell liable for 6% of the total site\nresponse cost.\n The Governments appealed the District Court’s appor\ntionment, and Shell cross-appealed the court’s finding of\nliability. The Court of Appeals acknow'
```

Suggested: `page_furniture`. Your verdict: ______

## 154/155: case 176, Burlington Northern & Santa Fe Railway Co. v. United States

> Because CERCLA does not specifically define what it means to "arrang[e] for" disposal of a hazardous substance, see, e.g., United States v. Cello-Foil Prods., Inc., 100 F. 3d 1227, 1231 (CA6 1996); Amcast Indus. Corp. v. Detrex Corp., 2 F. 3d 746, 751 (CA7 1993); Florida Power & Light Co., 893 F. 2d, at 1317, we give the phrase its ordinary meaning. In common parlance, the word "arrange" implies action directed to a specific purpose.

```
SOURCE GAP (4 ch): '[e] '
SOURCE GAP (143 ch): '. Crawford v. Metropolitan\nGovernment of Nashville and Davidson Cty., 555 U. S.\n____ (2009); Perrin v. United States, 444 U. S. 37, 42\n(1979). '
```

Suggested: `citation_omitted`. Your verdict: ______

## 155/155: case 177, Burlington Northern & Santa Fe Railway Co. v. United States

> Although the evidence adduced at trial showed that Shell was aware that minor, accidental spills occurred during the transfer of D–D from the common carrier to B&B's bulk storage tanks after the product had arrived at the Arvin facility and had come under B&B's stewardship, the evidence does not support an inference that Shell intended such spills to occur. To the contrary, the evidence revealed that Shell took numerous steps to encourage its distributors to reduce the likelihood of such spills, providing them with detailed safety manuals, requiring them to maintain adequate storage facilities, and providing discounts for those that took safety precautions. Although Shell's efforts were less than wholly successful, given these facts, Shell's mere knowledge that spills and leaks continued to occur is insufficient grounds for concluding that Shell "arranged for" the disposal of D–D within the meaning of §9607(a)(3).

```
SOURCE GAP (61 ch): ',\n Cite as: 556 U. S. ____ (2009) 13\n\n Opinion of the Court\n\n'
```

Suggested: `page_furniture`. Your verdict: ______
