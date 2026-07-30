import pandas as pd

import main
from quant_analysis import DataQualityError


def test_main_writes_alert_instead_of_rankings_on_quality_failure(
    monkeypatch, tmp_path
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        main,
        "get_stock_list",
        lambda: pd.DataFrame([{"symbol": "2330", "name": "台積電"}]),
    )
    monkeypatch.setattr(main, "download_batch", lambda _df: pd.DataFrame())
    monkeypatch.setattr(
        main,
        "score_and_rank",
        lambda _df: (_ for _ in ()).throw(DataQualityError("missing Close")),
    )

    main.main()

    report = (tmp_path / "report.html").read_text(encoding="utf-8")
    rankings = pd.read_csv(tmp_path / "final_rankings.csv")
    assert "台股報告資料異常" in report
    assert "missing Close" in report
    assert rankings.empty
