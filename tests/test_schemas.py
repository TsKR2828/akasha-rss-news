"""Phase 0 schema 驗收測試。

驗證：
1. 四個 schema 自己合法（meta-schema validation）。
2. 規格 §5.3 / §7.3 / §11.2 / §11.3 的樣本資料能通過對應 schema。
3. 規格 §17.1（P0）與 §17.2（voice_text lint）的關鍵限制能擋住違規資料。

對應規格：akashic-daily-report-final-spec-v1.1.md §17.1, §17.2, §17.3, §20.1
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, RefResolver, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = PROJECT_ROOT / "schemas"


# ---------------------------------------------------------------------------
# 1. 每個 schema 自己合法（meta-schema validation）
# ---------------------------------------------------------------------------

class TestSchemasAreValid:
    """規格 §17：四份 schema 必須通過 Draft 7 自我驗證。"""

    def test_article_schema_is_valid(self, article_schema):
        Draft7Validator.check_schema(article_schema)

    def test_event_schema_is_valid(self, event_schema):
        Draft7Validator.check_schema(event_schema)

    def test_platform_output_schema_is_valid(self, platform_output_schema):
        Draft7Validator.check_schema(platform_output_schema)

    def test_report_schema_is_valid(self, report_schema):
        Draft7Validator.check_schema(report_schema)


# ---------------------------------------------------------------------------
# 2. 樣本資料通過 schema
# ---------------------------------------------------------------------------

def _validator_for_report(report_schema, all_schemas):
    """report.schema.json 透過 $ref 指向 platform_output.schema.json，需 RefResolver。"""
    store = {schema["$id"]: schema for schema in all_schemas.values()}
    resolver = RefResolver.from_schema(report_schema, store=store)
    return Draft7Validator(report_schema, resolver=resolver)


class TestSamplesPass:
    def test_sample_article_passes(self, article_schema, sample_article):
        Draft7Validator(article_schema).validate(sample_article)

    def test_sample_event_passes(self, event_schema, sample_event):
        Draft7Validator(event_schema).validate(sample_event)

    def test_sample_platform_item_passes(self, platform_output_schema, sample_platform_item):
        Draft7Validator(platform_output_schema).validate(sample_platform_item)

    def test_sample_report_passes(self, report_schema, all_schemas, sample_report):
        validator = _validator_for_report(report_schema, all_schemas)
        validator.validate(sample_report)


# ---------------------------------------------------------------------------
# 3. P0 規則必須擋住違規資料（規格 §17.1 / §17.2 / §20.1）
# ---------------------------------------------------------------------------

class TestVoiceTextLint:
    """規格 §17.2：voice_text 不得含 URL、emoji 🧵 📌 📎、1/N、Markdown link。"""

    @pytest.mark.parametrize(
        "bad_voice_text",
        [
            "請見 https://example.com 詳情。",  # https URL
            "請見 http://example.com 詳情。",   # http URL
            "今天的 🧵 序號 1/2 是這樣的。",     # 🧵 emoji
            "📌 國際大事先講。",                # 📌 emoji
            "📎 附件如下。",                    # 📎 emoji
            "今天是 1/3 條新聞。",              # 1/N pattern
            "細節見[這裡](https://example.com)。",  # Markdown link
        ],
    )
    def test_bad_voice_text_fails(self, platform_output_schema, sample_platform_item, bad_voice_text):
        item = copy.deepcopy(sample_platform_item)
        item["voice_text"] = bad_voice_text
        item["platform_outputs"]["voice"]["text"] = bad_voice_text
        with pytest.raises(ValidationError):
            Draft7Validator(platform_output_schema).validate(item)


class TestPlatformCharLimits:
    """規格 §17.1：X 每則 ≤ 280、Threads 每則 ≤ 500。"""

    def test_x_post_over_280_chars_fails(self, platform_output_schema, sample_platform_item):
        item = copy.deepcopy(sample_platform_item)
        item["platform_outputs"]["x"]["posts"] = ["x" * 281]
        with pytest.raises(ValidationError):
            Draft7Validator(platform_output_schema).validate(item)

    def test_x_post_exactly_280_chars_passes(self, platform_output_schema, sample_platform_item):
        item = copy.deepcopy(sample_platform_item)
        item["platform_outputs"]["x"]["posts"] = ["x" * 280]
        Draft7Validator(platform_output_schema).validate(item)

    def test_threads_post_over_500_chars_fails(self, platform_output_schema, sample_platform_item):
        item = copy.deepcopy(sample_platform_item)
        item["platform_outputs"]["threads"]["posts"] = ["t" * 501]
        with pytest.raises(ValidationError):
            Draft7Validator(platform_output_schema).validate(item)

    def test_threads_post_exactly_500_chars_passes(self, platform_output_schema, sample_platform_item):
        item = copy.deepcopy(sample_platform_item)
        item["platform_outputs"]["threads"]["posts"] = ["t" * 500]
        Draft7Validator(platform_output_schema).validate(item)


class TestSourceRequirement:
    """規格 §17.1 / §20.1：每個 selected item 至少 1 個 source、1 條 claim_trace。"""

    def test_event_without_sources_fails(self, event_schema, sample_event):
        bad = copy.deepcopy(sample_event)
        bad["sources"] = []
        bad["source_count"] = 0
        with pytest.raises(ValidationError):
            Draft7Validator(event_schema).validate(bad)

    def test_event_without_claim_trace_fails(self, event_schema, sample_event):
        bad = copy.deepcopy(sample_event)
        bad["claim_trace"] = []
        with pytest.raises(ValidationError):
            Draft7Validator(event_schema).validate(bad)

    def test_platform_item_without_sources_fails(self, platform_output_schema, sample_platform_item):
        bad = copy.deepcopy(sample_platform_item)
        bad["sources"] = []
        with pytest.raises(ValidationError):
            Draft7Validator(platform_output_schema).validate(bad)

    def test_platform_item_without_claim_trace_fails(self, platform_output_schema, sample_platform_item):
        bad = copy.deepcopy(sample_platform_item)
        bad["claim_trace"] = []
        with pytest.raises(ValidationError):
            Draft7Validator(platform_output_schema).validate(bad)


class TestConditionalRules:
    """規格 §20.1 P0：tw_highlight=true 必有 reason；source_count=1 必標 single_source_warning。"""

    def test_tw_highlight_true_without_reason_fails(self, event_schema, sample_event):
        bad = copy.deepcopy(sample_event)
        bad["tw_highlight"] = True
        bad["tw_highlight_reason"] = None
        # 移除 tw_highlight_reason 欄位也應該 fail
        del bad["tw_highlight_reason"]
        with pytest.raises(ValidationError):
            Draft7Validator(event_schema).validate(bad)

    def test_tw_highlight_true_with_reason_passes(self, event_schema, sample_event):
        good = copy.deepcopy(sample_event)
        good["tw_highlight"] = True
        good["tw_highlight_reason"] = "Mentions TSMC and semiconductor supply chain."
        good["tw_highlight_keywords"] = ["TSMC", "supply chain"]
        Draft7Validator(event_schema).validate(good)

    def test_single_source_warning_must_be_true_when_count_is_one(
        self, platform_output_schema, sample_platform_item
    ):
        bad = copy.deepcopy(sample_platform_item)
        bad["source_count"] = 1
        bad["single_source_warning"] = False
        with pytest.raises(ValidationError):
            Draft7Validator(platform_output_schema).validate(bad)


class TestSourceFieldsRequired:
    """規格 §17.3：每個 source 必含 source_id / publisher / title / url / published_at。"""

    @pytest.mark.parametrize(
        "missing_field",
        ["source_id", "publisher", "title", "url", "published_at"],
    )
    def test_source_missing_required_field_fails(
        self, event_schema, sample_event, sample_source_ref, missing_field
    ):
        bad_source = {k: v for k, v in sample_source_ref.items() if k != missing_field}
        bad = copy.deepcopy(sample_event)
        bad["sources"] = [bad_source]
        bad["source_count"] = 1
        with pytest.raises(ValidationError):
            Draft7Validator(event_schema).validate(bad)


class TestStatusEnum:
    """規格 §17.1：status 必須為 ok | partial | failed。"""

    def test_invalid_status_fails(self, report_schema, all_schemas, sample_report):
        bad = copy.deepcopy(sample_report)
        bad["status"] = "success"  # invalid
        validator = _validator_for_report(report_schema, all_schemas)
        with pytest.raises(ValidationError):
            validator.validate(bad)

    @pytest.mark.parametrize("status", ["ok", "partial", "failed"])
    def test_valid_status_passes(self, report_schema, all_schemas, sample_report, status):
        good = copy.deepcopy(sample_report)
        good["status"] = status
        validator = _validator_for_report(report_schema, all_schemas)
        validator.validate(good)


class TestArticleIdHash:
    """article_id 必須是 sha256（64 hex chars）。"""

    def test_invalid_article_id_fails(self, article_schema, sample_article):
        bad = copy.deepcopy(sample_article)
        bad["article_id"] = "not-a-sha256"
        with pytest.raises(ValidationError):
            Draft7Validator(article_schema).validate(bad)

    def test_uppercase_hex_fails(self, article_schema, sample_article):
        # 規格規定小寫 hex（pattern: ^[a-f0-9]{64}$）
        bad = copy.deepcopy(sample_article)
        bad["article_id"] = "A" * 64
        with pytest.raises(ValidationError):
            Draft7Validator(article_schema).validate(bad)
