"""
SAKEC Outcome-Based Education Manual (Version 3.0) - Official Rubric Catalog & Microsoft Teams CSV Exporter.
Implements all official SAKEC Annexure B Rubrics (Section 25.1 to 25.8) and exports exact MS Teams-compatible .csv files.
"""

from typing import Any, Dict, List, Optional


# Official SAKEC OBE Manual Version 3.0 - Annexure B Rubric Catalog
SAKEC_OBE_RUBRICS_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "25.1.1 Computer-Allied Lab Experiment Rubric": [
        {
            "criterion": "Conceptual Understanding (Cognitive)",
            "weight": 20,
            "level_4": "Clearly explains objectives, theory, algorithms, tools and expected outcomes with strong clarity.",
            "level_3": "Explains objectives and concepts correctly with minor gaps.",
            "level_2": "Partial understanding; relies on lab manual or instructions.",
            "level_1": "Unable to explain purpose or underlying concept.",
        },
        {
            "criterion": "Execution (Psychomotor)",
            "weight": 15,
            "level_4": "Independently uses IDE, libraries and tools; code is correct, efficient and well-structured.",
            "level_3": "Executes code correctly with minor errors; minimal guidance required.",
            "level_2": "Frequent syntax/logical errors; needs repeated assistance.",
            "level_1": "Unable to execute experiment even with help.",
        },
        {
            "criterion": "Problem-Solving & Debugging (Cognitive + Psychomotor)",
            "weight": 20,
            "level_4": "Systematically identifies errors, debugs efficiently and optimizes solution.",
            "level_3": "Identifies errors and fixes them with guidance.",
            "level_2": "Struggles to locate or resolve errors.",
            "level_1": "No meaningful attempt to debug.",
        },
        {
            "criterion": "Professional Conduct & Lab Ethics (Affective)",
            "weight": 20,
            "level_4": "Highly disciplined, punctual, ethical; follows academic integrity and lab rules.",
            "level_3": "Generally disciplined with minor lapses.",
            "level_2": "Inconsistent discipline or over-dependence on peers.",
            "level_1": "Unprofessional behaviour; violates lab norms.",
        },
        {
            "criterion": "Output / Result Accuracy (Product)",
            "weight": 15,
            "level_4": "Output fully correct, validated and meets experiment objectives.",
            "level_3": "Output mostly correct with minor deviations.",
            "level_2": "Partially correct output.",
            "level_1": "Incorrect or no output.",
        },
        {
            "criterion": "Documentation & Result Analysis (Cognitive)",
            "weight": 10,
            "level_4": "Well-structured report with algorithm, code, screenshots, results and insightful analysis.",
            "level_3": "Complete documentation with basic analysis.",
            "level_2": "Incomplete or poorly explained report.",
            "level_1": "Very weak or missing documentation.",
        },
    ],
    "25.1.2 Circuit-Allied Lab Experiment Rubric": [
        {
            "criterion": "Conceptual Understanding & Circuit Planning (Cognitive)",
            "weight": 20,
            "level_4": "Clearly explains circuit theory, working principle, equations and expected output.",
            "level_3": "Explains basic working and theory with minor gaps.",
            "level_2": "Partial understanding; depends on manual.",
            "level_1": "Unable to explain circuit or objective.",
        },
        {
            "criterion": "Component Identification & Handling (Psychomotor)",
            "weight": 15,
            "level_4": "Correctly identifies components, ratings, polarity and handles them safely.",
            "level_3": "Minor identification or orientation errors corrected quickly.",
            "level_2": "Frequent component or connection mistakes.",
            "level_1": "Unable to identify or handle components properly.",
        },
        {
            "criterion": "Circuit Assembly & Troubleshooting (Cognitive + Psychomotor)",
            "weight": 20,
            "level_4": "Neat wiring; systematic fault-finding using instruments; resolves issues independently.",
            "level_3": "Correct assembly; troubleshooting with guidance.",
            "level_2": "Disorganized wiring; struggles to locate faults.",
            "level_1": "Incorrect assembly; unable to troubleshoot.",
        },
        {
            "criterion": "Safety, Discipline & Lab Conduct (Affective)",
            "weight": 20,
            "level_4": "Strictly follows safety procedures, power-up rules, grounding and discipline.",
            "level_3": "Generally safe with minor lapses.",
            "level_2": "Inconsistent safety practices.",
            "level_1": "Unsafe handling; violates lab safety norms.",
        },
        {
            "criterion": "Output Observation & Measurement Accuracy (Product)",
            "weight": 15,
            "level_4": "Observed output matches theory; accurate measurements using CRO/DSO/multimeter.",
            "level_3": "Output mostly correct within acceptable error.",
            "level_2": "Partially correct or unstable output.",
            "level_1": "No meaningful output observed.",
        },
        {
            "criterion": "Observation Table, Calculations & Conclusion (Cognitive)",
            "weight": 10,
            "level_4": "Complete observations, correct calculations, graphs and clear conclusion.",
            "level_3": "Minor errors in calculations or presentation.",
            "level_2": "Incomplete observations or weak analysis.",
            "level_1": "Poor or missing documentation.",
        },
    ],
    "25.1.3 PARIKSHAK - Test-Case-Based Program Evaluation Rubric": [
        {
            "criterion": "Test Case Pass Percentage (Cognitive + Psychomotor, Auto)",
            "weight": 60,
            "level_4": "Passes all test cases including edge and hidden cases.",
            "level_3": "Passes 75.00%-99.99% test cases.",
            "level_2": "Passes 50%-74.99% test cases.",
            "level_1": "Passes less than 50% test cases or runtime error.",
        },
        {
            "criterion": "Code Structure & Programming Practices (Psychomotor, Manual)",
            "weight": 20,
            "level_4": "Modular, readable code; proper indentation, naming and comments.",
            "level_3": "Mostly readable code with minor style issues.",
            "level_2": "Poor structure; limited readability.",
            "level_1": "Disorganized, unreadable or copied code.",
        },
        {
            "criterion": "Professional Conduct & Academic Integrity (Affective, Manual)",
            "weight": 20,
            "level_4": "Original work; ethical conduct; no plagiarism.",
            "level_3": "Minor guidance used; integrity maintained.",
            "level_2": "Over-dependence on peers/resources.",
            "level_1": "Plagiarized or unethical submission.",
        },
    ],
    "25.2.1 Semester Long Self-Learning Activity (SLA) - Individual": [
        {
            "criterion": "Problem Understanding & Design Methodology Formulation (Phase 1)",
            "weight": 25,
            "level_4": "Clear problem framing; well-structured, justified methodology.",
            "level_3": "Correct understanding with minor gaps.",
            "level_2": "Partial understanding; generic methodology.",
            "level_1": "Weak or incorrect methodology.",
        },
        {
            "criterion": "Methodology Validation - Implementation / Analytical Evidence (Phase 2)",
            "weight": 25,
            "level_4": "Strong validation using implementation or analytical evidence.",
            "level_3": "Adequate validation with minor issues.",
            "level_2": "Limited or superficial validation.",
            "level_1": "Validation missing or incorrect.",
        },
        {
            "criterion": "Methodology Evaluation, Trade-offs & Decision Rationale (Phase 3)",
            "weight": 20,
            "level_4": "Rigorous evaluation; justified decisions across scenarios and constraints.",
            "level_3": "Reasonable evaluation with limited scenarios.",
            "level_2": "Narrow or weak evaluation.",
            "level_1": "Arbitrary or unsupported decisions.",
        },
        {
            "criterion": "Final Comprehensive Report Quality",
            "weight": 15,
            "level_4": "Well-organized, coherent, technically sound report.",
            "level_3": "Minor clarity or structure issues.",
            "level_2": "Basic but acceptable report.",
            "level_1": "Incomplete or poorly structured.",
        },
        {
            "criterion": "Plagiarism & AI Usage Compliance",
            "weight": 10,
            "level_4": "Low similarity; transparent and ethical AI declaration.",
            "level_3": "Acceptable similarity; partial AI disclosure.",
            "level_2": "High similarity or unclear disclosure.",
            "level_1": "Plagiarism or unethical AI use.",
        },
        {
            "criterion": "Review Interaction & Defense",
            "weight": 5,
            "level_4": "Confident, evidence-based justification.",
            "level_3": "Minor gaps in defense.",
            "level_2": "Limited clarity.",
            "level_1": "Unable to justify.",
        },
    ],
    "25.2.2 Semester Long Self-Learning Activity (SLA) - Group": [
        {
            "criterion": "Problem Understanding & Design Methodology (Phase 1)",
            "weight": 25,
            "level_4": "Demonstrates deep, accurate understanding; methodology is coherent, justified, and integrates team insights.",
            "level_3": "Correct understanding with minor gaps; methodology mostly coherent.",
            "level_2": "Basic understanding; methodology basic with weak justification.",
            "level_1": "Misinterprets the problem; poorly defined methodology.",
        },
        {
            "criterion": "Contribution to Validation & Outcome Implementation (Phase 2)",
            "weight": 25,
            "level_4": "Strong, well-documented contribution; outcomes strongly validate methodology using implementation or analytical evidence.",
            "level_3": "Adequate contribution with minor gaps; outcomes mostly validate methodology.",
            "level_2": "Minimal contribution; partial or weak validation.",
            "level_1": "Negligible contribution; incorrect or missing validation.",
        },
        {
            "criterion": "Evaluation, Trade-offs & Decision Justification (Phase 3)",
            "weight": 20,
            "level_4": "Insightful evaluation; trade-offs clearly justified using evidence.",
            "level_3": "Reasonable evaluation across main scenarios.",
            "level_2": "Superficial evaluation.",
            "level_1": "Unsupported decisions.",
        },
        {
            "criterion": "Contribution to Final Report & Report Quality",
            "weight": 15,
            "level_4": "Clear, substantial contribution; well-structured, coherent, technically sound report.",
            "level_3": "Adequate contribution; minor gaps in structure.",
            "level_2": "Limited contribution; basic report.",
            "level_1": "Minimal contribution; poorly structured report.",
        },
        {
            "criterion": "Review Interaction, Defense & Learning Reflection",
            "weight": 10,
            "level_4": "Confident defense; clearly explains contribution and decisions with deep learning insights.",
            "level_3": "Clear reflection and explanation with minor gaps.",
            "level_2": "Limited clarity and generic reflection.",
            "level_1": "Unable to defend; minimal or irrelevant reflection.",
        },
        {
            "criterion": "Plagiarism & AI Compliance",
            "weight": 5,
            "level_4": "Acceptable similarity and ethical compliance.",
            "level_3": "Minor similarity issues.",
            "level_2": "Moderate similarity issues.",
            "level_1": "Plagiarism detected.",
        },
    ],
    "25.3 Case Study Activity Rubric": [
        {
            "criterion": "Problem Identification",
            "weight": 25,
            "level_4": "Clearly and comprehensively identify all key issues in the case.",
            "level_3": "Identifies most key issues with minor omissions.",
            "level_2": "Identifies some key issues but misses important points.",
            "level_1": "Fails to identify key issues or misunderstands the problem.",
        },
        {
            "criterion": "Analysis of Engineering Principles",
            "weight": 25,
            "level_4": "Demonstrates in-depth understanding and application of relevant engineering principles.",
            "level_3": "Shows good understanding and application of most relevant principles.",
            "level_2": "Basic application of some relevant principles with minor errors.",
            "level_1": "Poor understanding or misapplication of engineering principles.",
        },
        {
            "criterion": "Critical Thinking and Evaluation",
            "weight": 25,
            "level_4": "Strong evidence of critical thinking. Thorough and insightful evaluation of alternatives.",
            "level_3": "Some evidence of critical thinking. Evaluation of alternatives is present but may lack depth.",
            "level_2": "Limited evidence of critical thinking. Evaluation of alternatives is superficial.",
            "level_1": "No evidence of critical thinking and evaluation.",
        },
        {
            "criterion": "Conclusions and Recommendations",
            "weight": 25,
            "level_4": "Conclusions are well-supported and insightful. Recommendations are detailed, practical, and innovative.",
            "level_3": "Conclusions are mostly supported by the analysis. Recommendations are relevant but may lack detail.",
            "level_2": "Conclusions are vague or unsupported. Recommendations are limited or impractical.",
            "level_1": "Poor conclusions and recommendations.",
        },
    ],
    "25.4 Presentation Activity Rubric": [
        {
            "criterion": "Content and Technical Accuracy (GA)",
            "weight": 20,
            "level_4": "Comprehensive and accurate content; demonstrates deep understanding of the topic.",
            "level_3": "Mostly accurate content; demonstrates good understanding of the topic.",
            "level_2": "Basic content covered; some inaccuracies are present.",
            "level_1": "Limited or inaccurate content; poor understanding is evident.",
        },
        {
            "criterion": "Organization and Flow (GA)",
            "weight": 20,
            "level_4": "Logical and coherent structure; smooth transitions between ideas.",
            "level_3": "Clear structure; mostly smooth transitions.",
            "level_2": "Basic structure present; some abrupt transitions.",
            "level_1": "Poor organization; lacks clear structure and flow.",
        },
        {
            "criterion": "Visual Design and Use of Media (GA)",
            "weight": 20,
            "level_4": "Visually appealing; effective use of graphics, charts, and animations.",
            "level_3": "Good visual design; appropriate use of media.",
            "level_2": "Basic design; limited use of visual aids.",
            "level_1": "Poor design; ineffective or distracting use of media.",
        },
        {
            "criterion": "Delivery and Presentation Skills (IA)",
            "weight": 20,
            "level_4": "Confident and engaging delivery; excellent time management.",
            "level_3": "Clear delivery; good eye contact and timing.",
            "level_2": "Adequate delivery; some hesitation or rushing.",
            "level_1": "Poor delivery; lacks engagement and significant timing issues.",
        },
        {
            "criterion": "Q&A and Technical Knowledge (GA)",
            "weight": 20,
            "level_4": "Answers all questions with depth and insight; demonstrates extensive knowledge.",
            "level_3": "Answers most questions well; shows good knowledge.",
            "level_2": "Answers some questions adequately; basic knowledge is evident.",
            "level_1": "Struggles to answer questions; limited knowledge demonstrated.",
        },
    ],
    "25.5 Micro-Project Activity Rubric": [
        {
            "criterion": "Problem Definition & Scope",
            "weight": 20,
            "level_4": "Clearly defined problem with a focused and achievable scope.",
            "level_3": "Problem identified, but scope may be unclear or too broad/narrow.",
            "level_2": "Problem vaguely defined, or scope is missing.",
            "level_1": "Problem not clearly identified or missing.",
        },
        {
            "criterion": "Design & Methodology",
            "weight": 20,
            "level_4": "Innovative and well-structured approach with justification for chosen methods.",
            "level_3": "Appropriate design and methodology, but limited justification.",
            "level_2": "Basic design and methodology, with some justification.",
            "level_1": "Weak or missing design and methodology.",
        },
        {
            "criterion": "Implementation & Results",
            "weight": 20,
            "level_4": "Project completed effectively with clear and well-presented results.",
            "level_3": "Project completed but results are unclear or poorly presented.",
            "level_2": "Project partially completed with limited or unclear results.",
            "level_1": "Project not completed or results are missing.",
        },
        {
            "criterion": "Analysis & Interpretation",
            "weight": 20,
            "level_4": "Thorough analysis with insightful interpretation of results.",
            "level_3": "Analysis attempted, but interpretation could be improved.",
            "level_2": "Basic analysis with limited interpretation.",
            "level_1": "Weak or missing analysis and interpretation.",
        },
        {
            "criterion": "Report & Presentation",
            "weight": 20,
            "level_4": "Clear, concise, and well-organized report with effective presentation.",
            "level_3": "Report is generally well-written but may lack clarity or organization. Presentation could be improved.",
            "level_2": "Report lacks clarity or organization. Presentation needs significant improvement.",
            "level_1": "Poorly written report with ineffective or missing presentation.",
        },
    ],
    "25.6 Group Discussion Activity Rubric": [
        {
            "criterion": "Subject Knowledge",
            "weight": 20,
            "level_4": "Demonstrates comprehensive understanding of the topic; provides insightful contributions.",
            "level_3": "Shows good understanding of the topic; makes relevant points.",
            "level_2": "Basic understanding of the topic; provides some relevant contributions.",
            "level_1": "Limited understanding; contributions are off-topic or inaccurate.",
        },
        {
            "criterion": "Communication Skills",
            "weight": 20,
            "level_4": "Articulates ideas clearly and concisely; demonstrates excellent verbal and non-verbal communication.",
            "level_3": "Communicates ideas effectively; demonstrates good verbal and non-verbal skills.",
            "level_2": "Adequate communication; some clarity issues are observed.",
            "level_1": "Poor communication; ideas are unclear or difficult to understand.",
        },
        {
            "criterion": "Participation and Initiative",
            "weight": 20,
            "level_4": "Actively participates throughout the discussion; initiates discussions and involves others.",
            "level_3": "Participates regularly; occasionally initiates discussions.",
            "level_2": "Participates when prompted; rarely initiates discussions.",
            "level_1": "Minimal participation; does not initiate discussions.",
        },
        {
            "criterion": "Listening and Responsiveness",
            "weight": 20,
            "level_4": "Actively listens to others; builds upon or respectfully challenges others' ideas.",
            "level_3": "Listens well; generally responds appropriately to others' points.",
            "level_2": "Sometimes listens; occasionally responds to others.",
            "level_1": "Poor listening skills; rarely responds to or acknowledges others.",
        },
        {
            "criterion": "Critical Thinking and Problem-Solving",
            "weight": 20,
            "level_4": "Analyzes issues deeply; proposes innovative and effective solutions.",
            "level_3": "Provides good analysis of issues; suggests practical solutions.",
            "level_2": "Provides basic analysis; attempts to propose solutions.",
            "level_1": "Limited analysis; does not propose solutions.",
        },
    ],
    "25.7 Scenario-Based Assignment Activity Rubric": [
        {
            "criterion": "Understanding of Scenario/Problem Context",
            "weight": 20,
            "level_4": "Demonstrates clear understanding of the given scenario/problem; correctly identifies key issues, constraints, and objectives.",
            "level_3": "Demonstrates good understanding; identifies most relevant aspects of the scenario.",
            "level_2": "Shows basic understanding; identifies some key elements.",
            "level_1": "Shows minimal understanding; fails to identify key elements of the scenario.",
        },
        {
            "criterion": "Analysis & Application of Concepts",
            "weight": 30,
            "level_4": "Applies relevant technical/engineering knowledge to analyze the scenario; demonstrates logical reasoning and may include diagrams, calculations, or references.",
            "level_3": "Applies mostly relevant technical knowledge with minor errors or gaps.",
            "level_2": "Applies basic or partially relevant concepts; analysis is present but limited in clarity.",
            "level_1": "Analysis is weak, incomplete, or mostly incorrect.",
        },
        {
            "criterion": "Solution / Decision-Making & Justification",
            "weight": 30,
            "level_4": "Provides a feasible and well-thought-out solution; justifies the approach using data, theory, or best practices.",
            "level_3": "Provides a valid solution; justification lacks strong supporting evidence.",
            "level_2": "Provides a basic or partially feasible solution; justification is weak.",
            "level_1": "Provides a vague, unclear, or impractical solution with little to no justification.",
        },
        {
            "criterion": "Report / Assignment Quality",
            "weight": 20,
            "level_4": "Clear, concise, and well-organized report demonstrating effective presentation of ideas.",
            "level_3": "Report is generally well-written but may lack clarity or organization.",
            "level_2": "Report lacks clarity or organization.",
            "level_1": "Poorly written report with inadequate presentation.",
        },
    ],
    "25.8 Reel / Blog / Skit Activity Rubric (5 Criteria - MS Teams Standard)": [
        {
            "criterion": "Clarity of Concept ",
            "weight": 30,
            "level_4": "Concept is clearly explained with accurate examples and appropriate interpretation.",
            "level_3": "Concept is clearly explained with relevant information.",
            "level_2": "Concept explanation is inadequate or lacks clarity.",
            "level_1": "Concept explanation is incorrect or demonstrates misunderstanding.",
        },
        {
            "criterion": "Creativity & Engagement ",
            "weight": 20,
            "level_4": "Highly creative, visually appealing, and strongly engaging presentation.",
            "level_3": "Creative approach with moderate engagement and visualization.",
            "level_2": "Basic visualization with limited creativity.",
            "level_1": "Dull or ineffective visualization with poor engagement.",
        },
        {
            "criterion": "Technical Content (Simulation/Logic) ",
            "weight": 20,
            "level_4": "Relevant code and logic are correctly used with proper comments, structure, and indentation.",
            "level_3": "Correct code and logic are used but comments or indentation require improvement.",
            "level_2": "Code addresses some conditions but does not completely satisfy all requirements.",
            "level_1": "Poor code quality; code does not execute or fails to address basic conditions.",
        },
        {
            "criterion": "Communication & Presentation ",
            "weight": 15,
            "level_4": "Smooth, confident, and audience-friendly communication.",
            "level_3": "Clear communication with minor hesitation.",
            "level_2": "Basic effort in communication and presentation.",
            "level_1": "Low effort with ineffective communication.",
        },
        {
            "criterion": "Real-world Connection / Metaphor ",
            "weight": 15,
            "level_4": "Strong metaphor or real-world scenario is used to explain the concept effectively.",
            "level_3": "Good connection with a scenario, but some conditions or scope limitations are missing.",
            "level_2": "Basic connection is demonstrated but scope is unclear.",
            "level_1": "Connection is irrelevant or missing.",
        },
    ],
    "25.8 Reel / Blog / Skit Activity Rubric (7 Criteria - Group & Peer Voting)": [
        {
            "criterion": "Clarity of Concept (GA)",
            "weight": 30,
            "level_4": "Concept is clearly explained with accurate examples and appropriate interpretation.",
            "level_3": "Concept is clearly explained with relevant information.",
            "level_2": "Concept explanation is inadequate or lacks clarity.",
            "level_1": "Concept explanation is incorrect or demonstrates misunderstanding.",
        },
        {
            "criterion": "Creativity & Engagement (GA)",
            "weight": 15,
            "level_4": "Highly creative, visually appealing, and strongly engaging presentation.",
            "level_3": "Creative approach with moderate engagement and visualization.",
            "level_2": "Basic visualization with limited creativity.",
            "level_1": "Dull or ineffective visualization with poor engagement.",
        },
        {
            "criterion": "Technical Content (Code/Logic) (GA)",
            "weight": 15,
            "level_4": "Relevant code and logic are correctly used with proper comments, structure, and indentation.",
            "level_3": "Correct code and logic are used but comments or indentation require improvement.",
            "level_2": "Code addresses some conditions but does not completely satisfy all requirements.",
            "level_1": "Poor code quality; code does not execute or fails to address basic conditions.",
        },
        {
            "criterion": "Communication & Presentation (GA)",
            "weight": 15,
            "level_4": "Smooth, confident, and audience-friendly communication.",
            "level_3": "Clear communication with minor hesitation.",
            "level_2": "Basic effort in communication and presentation.",
            "level_1": "Low effort with ineffective communication.",
        },
        {
            "criterion": "Real-world Connection / Metaphor (GA)",
            "weight": 15,
            "level_4": "Strong metaphor or real-world scenario is used to explain the concept effectively.",
            "level_3": "Good connection with a scenario, but some conditions or scope limitations are missing.",
            "level_2": "Basic connection is demonstrated but scope is unclear.",
            "level_1": "Connection is irrelevant or missing.",
        },
        {
            "criterion": "Team Collaboration (IA)",
            "weight": 5,
            "level_4": "All members contribute effectively, demonstrate coordination, and support each other throughout the activity.",
            "level_3": "Most members contribute and coordinate effectively with minor gaps.",
            "level_2": "Limited collaboration with uneven participation.",
            "level_1": "Poor collaboration and minimal team involvement.",
        },
        {
            "criterion": "Peer Voting (IA)",
            "weight": 5,
            "level_4": "Highly appreciated by peers for content quality, creativity, communication, and overall impact.",
            "level_3": "Received positive peer feedback with good overall performance.",
            "level_2": "Moderate peer appreciation with scope for improvement.",
            "level_1": "Limited peer appreciation and low overall impact.",
        },
    ],
}


def generate_ms_teams_rubric_csv(title: str, criteria_list: List[Dict[str, Any]], total_points: int = 100) -> str:
    """
    Formats a list of rubric criteria into the exact Microsoft Teams Rubric CSV import schema (v.11p).
    Every criterion produces 2 rows:
      Row 1: "<criterion>","<level_4>",,"<level_3>",,"<level_2>",,"<level_1>",
      Row 2: "<weight>"
    """
    def _escape_csv_str(val: Any) -> str:
        s = str(val or "").replace('"', '""')
        return f'"{s}"'

    lines = [
        '"For the best editing experience, upload this .csv as a rubric in Microsoft Teams."',
        "",
        f'{_escape_csv_str(title)},"{total_points}"',
        '""',
        '""',
        ',"","4","","3","","2","","1"',
    ]

    for item in criteria_list:
        crit = item.get("criterion", "Criterion")
        l4 = item.get("level_4") or item.get("exemplary_4", "")
        l3 = item.get("level_3") or item.get("proficient_3", "")
        l2 = item.get("level_2") or item.get("developing_2", "")
        l1 = item.get("level_1") or item.get("novice_1", "")
        weight = int(item.get("weight", 20))

        row1 = f'{_escape_csv_str(crit)},{_escape_csv_str(l4)},,{_escape_csv_str(l3)},,{_escape_csv_str(l2)},,{_escape_csv_str(l1)},'
        row2 = f'"{weight}"'
        lines.append(row1)
        lines.append(row2)

    lines.append("v.11p")
    return "\n".join(lines) + "\n"
