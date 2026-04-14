# Manual Revision Examples

This document collects representative examples from the manual adjudication and third-round cleanup process for the benchmark dataset.

It is intended for:

- `README` excerpts
- paper appendix examples
- annotation guideline refinement
- explaining why the dataset is not a purely automatic expansion product

## What Was Revised

The cleanup process focused on four recurring problems in auto-expanded samples:

1. Template-like answers
2. Generic claims that were not independently verifiable
3. Multi-authority questions with no division of labor between sources
4. Wrong or low-value citations caused by noisy article selection

The target style after revision is:

- each `claim_text` is a concrete legal proposition
- each claim can be checked against one or more specific citations
- exception, condition, prohibition, and procedure are separated when needed
- multi-source questions explain what each source contributes
- obviously wrong citations are replaced rather than cosmetically rewritten

## Revision Rules

The manual cleanup followed these rules:

1. Do not keep meta-text such as "the answer should explain conditions" as gold claims.
2. Do not use a citation only because it is nearby or scored high; use it only if it really supports the claim.
3. If a question is not truly an "exception clause" question, rewrite it as a boundary, prohibition, trigger, or procedural-duty question.
4. For multi-authority questions, specify which source supports which part of the conclusion.
5. Prefer 2-3 concrete claims over one vague umbrella claim.

## Example 1: Exception Question From Template To Concrete

Sample: `sample_0089`

File:
- [benchmark_dev.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_dev.jsonl)

Before:

```json
{
  "reference_answer": "根据《电信互联网个信保护规定》，应先确认一般规则，再结合条文中的例外或但书判断是否可以作出偏离一般规则的处理。",
  "claims": [
    {"claim_text": "电信业务经营者、互联网信息服务提供者收集、使用用户个人信息的，应当明确告知用户..."},
    {"claim_text": "法律、行政法规对本条第一款至第四款规定的情形另有规定的，从其规定"},
    {"claim_text": "回答中应明确说明一般规则与例外边界，避免将一般规则绝对化"}
  ]
}
```

After:

```json
{
  "reference_answer": "《电信互联网个信保护规定》并不是只要求“先同意再处理”。更完整的边界是：原则上未经用户同意不得收集、使用个人信息；即便取得同意，也只能在告知目的、方式、范围并限于提供服务所必需的范围内处理；如果法律、行政法规对相关情形另有规定，则从其规定。",
  "claims": [
    {
      "claim_text": "原则上，未经用户同意，电信业务经营者和互联网信息服务提供者不得收集、使用用户个人信息。",
      "gold_citations": ["rule_telecom_internet_pi_2013_art009"]
    },
    {
      "claim_text": "即使取得用户同意，也不得收集提供服务所必需以外的个人信息，不得将信息用于提供服务之外的目的。",
      "gold_citations": ["rule_telecom_internet_pi_2013_art009"]
    },
    {
      "claim_text": "法律、行政法规对相关情形另有规定的，从其规定，因此“取得同意”不是所有场景下唯一的处理依据。",
      "gold_citations": ["rule_telecom_internet_pi_2013_art009"]
    }
  ]
}
```

Why this is better:

- the baseline rule and the carve-out are separated
- each claim can be checked independently
- the sample can detect both omission and overclaim

## Example 2: Wrong Citation Repair

Sample: `sample_0008`

File:
- [benchmark_train.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_train.jsonl)

Problem before revision:

- citation pointed to `law_pipl_2021_art080`, which was actually a legislative explanation artifact
- claim text described the necessity of legislation rather than a procedural duty

After:

```json
{
  "gold_authorities": [
    "law_pipl_2021_art055",
    "law_pipl_2021_art056",
    "law_pipl_2021_art061"
  ],
  "reference_answer": "依据《个人信息保护法》，关键程序性义务至少包括：建立便捷的个人权利申请受理和处理机制；根据处理目的、处理方式、个人信息种类和风险采取内部管理、分类管理、加密、培训和应急预案等保护措施；在处理敏感个人信息、自动化决策、委托处理、向境外提供个人信息等高风险场景下，事前进行个人信息保护影响评估并留存记录。",
  "claims": [
    {
      "claim_text": "个人信息处理者应当建立便捷的个人行使权利的申请受理和处理机制；拒绝个人行使权利请求的，应当说明理由。",
      "gold_citations": ["law_pipl_2021_art055"]
    },
    {
      "claim_text": "个人信息处理者应当根据处理目的、处理方式、个人信息种类以及对个人权益的影响和安全风险，制定内部管理制度、分类管理、采取加密和去标识化等技术措施、培训人员并制定应急预案。",
      "gold_citations": ["law_pipl_2021_art056"]
    },
    {
      "claim_text": "处理敏感个人信息、利用个人信息进行自动化决策、委托处理、向其他处理者提供、公开或者向境外提供个人信息，以及其他对个人权益有重大影响的活动前，个人信息处理者应当事前进行个人信息保护影响评估，并对处理情况进行记录。",
      "gold_citations": ["law_pipl_2021_art061"]
    }
  ]
}
```

Why this matters:

- this is not just style polishing
- it repairs a genuinely wrong citation
- after repair, the sample tests procedural compliance instead of legislative background

## Example 3: Multi-Authority Division Of Labor

Sample: `sample_0015`

File:
- [benchmark_train.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_train.jsonl)

Before:

```json
{
  "reference_answer": "本题需要将《算法推荐规定》和《网安审查办法》分别对应到不同义务模块，再进行联合适用。",
  "claims": [
    {"claim_text": "《算法推荐规定》中的一项义务"},
    {"claim_text": "《网安审查办法》中的一项义务"},
    {"claim_text": "需联合两法源交叉验证"}
  ]
}
```

After:

```json
{
  "reference_answer": "结合《算法推荐规定》与《网安审查办法》时，不能只讲算法前台告知，也不能只讲国家安全审查。前者解决的是用户知情、关闭和标签管理，后者解决的是采购网络产品和服务时，何时因国家安全风险启动审查以及申报材料要求。",
  "claims": [
    {
      "claim_text": "算法推荐服务提供者应当以显著方式告知用户其提供算法推荐服务的情况，并以适当方式公示算法推荐服务的基本原理、目的意图和主要运行机制等。",
      "gold_citations": ["rule_algo_recommend_2021_art016"]
    },
    {
      "claim_text": "算法推荐服务提供者应当向用户提供不针对其个人特征的选项或者便捷的关闭算法推荐服务选项，并提供选择或者删除用户标签的功能。",
      "gold_citations": ["rule_algo_recommend_2021_art017"]
    },
    {
      "claim_text": "如果算法推荐服务所依赖的网络产品或者服务影响或者可能影响国家安全，运营者除履行前述用户知情和控制义务外，还应向网络安全审查办公室申报网络安全审查，并提交国家安全风险分析报告和采购文件等材料。",
      "gold_citations": [
        "rule_algo_recommend_2021_art016",
        "rule_algo_recommend_2021_art017",
        "rule_cybersecurity_review_2021_art005",
        "rule_cybersecurity_review_2021_art007"
      ]
    }
  ]
}
```

Why this is better:

- the first source governs user-facing algorithm obligations
- the second source governs review trigger and filing materials
- the combined claim explains why one source alone is insufficient

## Example 4: Condition Question With Real Legal Thresholds

Sample: `sample_0032`

Files:
- [benchmark_train.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_train.jsonl)
- [benchmark_dev.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_dev.jsonl) for the parallel procedural variant `sample_0092`

After:

```json
{
  "reference_answer": "判断在什么条件下《民法典》允许或者要求处理个人信息，至少要看三个层面：一是处理个人信息应满足合法、正当、必要、同意、公开规则和明示目的等条件；二是在特定情况下行为人可以不承担民事责任；三是自然人对其个人信息享有查阅、复制、更正和删除等请求权。",
  "claims": [
    {
      "claim_text": "处理个人信息的，应当遵循合法、正当、必要原则，不得过度处理，并符合征得同意、公开规则、明示目的方式范围和不违反法律法规及约定等条件。",
      "gold_citations": ["law_civil_code_privacy_pi_2020_art1077"]
    },
    {
      "claim_text": "在自然人或者其监护人同意范围内合理实施、合理处理自然人自行公开或者其他已经合法公开的信息，或者为维护公共利益、该自然人合法权益而合理实施其他行为的，行为人不承担民事责任。",
      "gold_citations": ["law_civil_code_privacy_pi_2020_art1078"]
    },
    {
      "claim_text": "自然人可以依法向信息处理者查阅、复制其个人信息；发现信息有错误的，有权提出异议并请求及时更正；发现违法或者违约处理个人信息的，有权请求及时删除。",
      "gold_citations": ["law_civil_code_privacy_pi_2020_art1079"]
    }
  ]
}
```

Why this is useful in evaluation:

- it distinguishes lawful processing conditions from non-liability situations
- it also captures the downstream rights that a model may omit

## Example 5: Procedure-Focused Question

Sample: `sample_0092`

After:

```json
{
  "reference_answer": "依据《民法典》隐私权和个人信息保护条款，关键程序性义务主要包括：及时响应查阅、复制、更正、删除等请求；采取技术措施和其他必要措施保障个人信息安全并在发生风险时采取补救和告知措施；国家机关及其工作人员对履职中知悉的隐私和个人信息负有保密义务。",
  "claims": [
    {
      "claim_text": "自然人可以依法向信息处理者查阅、复制其个人信息；发现信息有错误的，有权提出异议并请求及时更正；发现违法或者违约处理个人信息的，有权请求及时删除。",
      "gold_citations": ["law_civil_code_privacy_pi_2020_art1079"]
    },
    {
      "claim_text": "信息处理者应当采取技术措施和其他必要措施，确保其收集、存储的个人信息安全，防止信息泄露、篡改、丢失；发生或者可能发生相关风险的，应当及时采取补救措施并按规定告知自然人、向有关主管部门报告。",
      "gold_citations": ["law_civil_code_privacy_pi_2020_art1080"]
    },
    {
      "claim_text": "国家机关、承担行政职能的法定机构及其工作人员，对于履行职责过程中知悉的自然人的隐私和个人信息，应当予以保密，不得泄露或者向他人非法提供。",
      "gold_citations": ["law_civil_code_privacy_pi_2020_art1081"]
    }
  ]
}
```

What this example shows:

- a procedural question does not need to be abstract
- it can still be built from independently checkable claims

## Example 6: Direct-Law Question Cleanup

Sample: `sample_0119`

File:
- [benchmark_test.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_test.jsonl)

After:

```json
{
  "reference_answer": "根据该规范，完整回答至少应覆盖三个层面：一是未经用户同意不得收集、使用用户个人信息，并受必要性和用途限制约束；二是主管机关可以开展监督检查，经营者、服务提供者应予配合；三是收集、使用过程中形成的用户个人信息应严格保密，不得泄露、篡改、毁损或者非法提供。",
  "claims": [
    {
      "claim_text": "未经用户同意，电信业务经营者、互联网信息服务提供者不得收集、使用用户个人信息。收集、使用时，应明确告知目的、方式和范围，不得收集提供服务所必需以外的个人信息或者用于提供服务之外的目的。",
      "gold_citations": ["rule_telecom_internet_pi_2013_art009"]
    },
    {
      "claim_text": "电信管理机构可以对个人信息保护情况实施监督检查，被检查的电信业务经营者、互联网信息服务提供者应当予以配合；监督检查不得妨碍正常经营或者服务活动，不得收取任何费用。",
      "gold_citations": ["rule_telecom_internet_pi_2013_art017"]
    },
    {
      "claim_text": "电信业务经营者、互联网信息服务提供者及其工作人员对在提供服务过程中收集、使用的用户个人信息应当严格保密，不得泄露、篡改、毁损，不得出售或者非法向他人提供。",
      "gold_citations": ["rule_telecom_internet_pi_2013_art010"]
    }
  ]
}
```

Why this works well for benchmark display:

- it reads like a real legal answer
- it still retains claim-level evaluation granularity

## Suggested Use In README

You can cite this file together with one short explanation such as:

> The benchmark was not released as a raw automatic expansion output. We manually revised template-like samples into claim-level gold examples with concrete propositions, corrected mis-selected citations, and explicitly decomposed multi-authority questions into source-specific subclaims.

## Suggested Use In Paper

A compact description that fits well in a paper appendix:

> We performed post-generation human adjudication to convert draft samples into evaluation-grade gold instances. The adjudication focused on citation correction, exception concretization, claim decomposability, and multi-source division of labor. Representative examples are provided in `manual_revision_examples.md`.

## Related Files

- [benchmark_train.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_train.jsonl)
- [benchmark_dev.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_dev.jsonl)
- [benchmark_test.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_test.jsonl)
- [claim_annotation_template.jsonl](/c:/Users/H/Desktop/docker/lawllm/annotation/claim_annotation_template.jsonl)


## Example 5: OCR Fragment Repair

Sample: `sample_0096`

Files:
- [benchmark_dev.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/benchmark_dev.jsonl)
- [authority_articles.jsonl](/c:/Users/H/Desktop/docker/lawllm/data_processed/authority_articles.jsonl)

Problem before revision:

- the cited article text had OCR/page-break residue such as `?????????`
- the claim inherited raw fragment text instead of a checkable legal proposition
- the reference answer also kept the fragment and an ellipsis-style summary

After revision:

```json
{
  "reference_answer": "???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????45??????????????????????????????????????????????????????????????????",
  "claims": [
    {
      "claim_text": "???????????????????????????????????????????????????????????????????????????????????45????????????????"
    }
  ]
}
```

Why this matters:

- public examples should not expose OCR residue as if it were gold text
- a benchmark claim must remain judgeable even when the underlying raw parse is noisy
- this kind of repair is a good illustration of why final gold cannot rely on automatic expansion alone
