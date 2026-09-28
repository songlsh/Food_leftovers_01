from pathlib import Path
from app.event import EventRecord

class ReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)

    def generate(self, event_or_record):
        record = event_or_record if isinstance(event_or_record, EventRecord) else EventRecord.from_event(event_or_record)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"{record.event_id}.txt"
        lines = ["====================", "剩菜检测报告", "", f"事件: {record.event_id}", f"时间: {record.time}", f"状态: {record.status}", f"总剩余: {record.total_weight:.1f}g", "", "检测结果:"]
        for c in record.cells:
            conf = "-" if c.confidence is None else f"{c.confidence * 100:.0f}%"
            lines += [f"{c.cell_id}. {c.food_id or 'UNKNOWN'}", f"重量: {c.net_weight if c.net_weight is not None else 0:.1f}g", f"AI置信度: {conf}", ""]
        lines.append("====================")
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    def generate_statistics_xlsx(self, statistics_service, query, suggestions=None, output_path=None):
        """Export a complete statistics report as a real Excel workbook."""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.formatting.rule import ColorScaleRule
            from openpyxl.utils import get_column_letter
        except ImportError as exc:
            raise RuntimeError("导出 Excel 需要 openpyxl，请先运行：pip install openpyxl") from exc

        self.output_dir.mkdir(parents=True, exist_ok=True)
        if output_path is None:
            output_path = self.output_dir / "剩菜统计报告.xlsx"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        summary = statistics_service.get_summary(query)
        foods = statistics_service.get_food_statistics(query)
        daily = statistics_service.get_daily_statistics(query)
        suggestions = suggestions or []

        wb=Workbook(); ws=wb.active; ws.title="统计总览"
        thin=Side(style="thin", color="D9E1E8")
        header_fill=PatternFill("solid", fgColor="1F4E78")
        section_fill=PatternFill("solid", fgColor="D9EAF7")
        title_font=Font(size=18,bold=True,color="FFFFFF")
        header_font=Font(bold=True,color="FFFFFF")

        ws.merge_cells("A1:H1"); ws["A1"]="剩菜统计分析报告"; ws["A1"].font=title_font; ws["A1"].fill=header_fill; ws["A1"].alignment=Alignment(horizontal="center")
        ws["A3"]="统计开始"; ws["B3"]=query.start_time.strftime("%Y-%m-%d %H:%M:%S") if query.start_time else "不限"
        ws["D3"]="统计结束"; ws["E3"]=query.end_time.strftime("%Y-%m-%d %H:%M:%S") if query.end_time else "不限"
        ws["A5"]="核心指标"; ws["A5"].fill=section_fill; ws["A5"].font=Font(bold=True,size=13)
        metrics=[("事件数量",summary.event_count,"0"),("初始总重量(g)",summary.total_initial_weight,"0.0"),("总剩余重量(g)",summary.total_remaining_weight,"0.0"),("总消耗量(g)",summary.total_consumed_weight,"0.0"),("剩余率",summary.remaining_rate,"0.0%"),("消耗率",summary.consumption_rate,"0.0%")]
        for i,(name,val,fmt) in enumerate(metrics, start=6):
            ws.cell(i,1,name).font=Font(bold=True); ws.cell(i,2,val if val is not None else "-"); ws.cell(i,2).number_format=fmt
            ws.cell(i,1).border=ws.cell(i,2).border=Border(bottom=thin)
        ws["D5"]="自动建议"; ws["D5"].fill=section_fill; ws["D5"].font=Font(bold=True,size=13)
        for idx,s in enumerate(suggestions or ["当前数据未命中配置规则。"], start=6):
            ws.merge_cells(start_row=idx,start_column=4,end_row=idx,end_column=8); ws.cell(idx,4,s).alignment=Alignment(wrap_text=True,vertical="top")

        wf=wb.create_sheet("食物统计"); headers=["食物ID","食物名称","格位数","初始重量(g)","剩余重量(g)","消耗量(g)","剩余率","消耗率","建议"]
        wf.append(headers)
        for c in wf[1]: c.fill=header_fill; c.font=header_font; c.alignment=Alignment(horizontal="center")
        for x in foods:
            sg=[]
            if suggestions:
                sg=[s for s in suggestions if x.food_name in s]
            wf.append([x.food_id or "",x.food_name,x.count,x.total_initial_weight,x.total_remaining_weight,x.total_consumed_weight if x.total_consumed_weight is not None else "-",x.remaining_rate if x.remaining_rate is not None else "-",x.consumption_rate if x.consumption_rate is not None else "-","；".join(sg) or "-"])
        for row in wf.iter_rows(min_row=2):
            row[6].number_format=row[7].number_format="0.0%"
            for cell in row: cell.border=Border(bottom=thin); cell.alignment=Alignment(vertical="top",wrap_text=True)
        wf.freeze_panes="A2"; wf.auto_filter.ref=wf.dimensions
        if wf.max_row>1: wf.conditional_formatting.add(f"G2:G{wf.max_row}",ColorScaleRule(start_type='min',start_color='63BE7B',mid_type='percentile',mid_value=50,mid_color='FFEB84',end_type='max',end_color='F8696B'))

        wd=wb.create_sheet("每日统计"); headers=["日期","事件数量","初始重量(g)","剩余重量(g)","消耗量(g)","剩余率","消耗率"]
        wd.append(headers)
        for c in wd[1]: c.fill=header_fill; c.font=header_font; c.alignment=Alignment(horizontal="center")
        for x in daily:
            wd.append([x.date,x.event_count,x.total_initial_weight,x.total_remaining_weight,x.total_consumed_weight if x.total_consumed_weight is not None else "-",x.remaining_rate if x.remaining_rate is not None else "-",x.consumption_rate if x.consumption_rate is not None else "-"])
        for row in wd.iter_rows(min_row=2):
            row[5].number_format=row[6].number_format="0.0%"
            for cell in row: cell.border=Border(bottom=thin)
        wd.freeze_panes="A2"; wd.auto_filter.ref=wd.dimensions

        for sh in wb.worksheets:
            sh.sheet_view.showGridLines=False
            for col in range(1,sh.max_column+1):
                max_len=max([len(str(sh.cell(r,col).value or "")) for r in range(1,min(sh.max_row,100)+1)] or [8])
                sh.column_dimensions[get_column_letter(col)].width=min(max(max_len+2,10),36)
        wb.save(output_path)
        return str(output_path)
