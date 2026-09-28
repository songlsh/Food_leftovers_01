from __future__ import annotations
from datetime import datetime, time
from pathlib import Path
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import *
from app.statistics import StatisticsQuery, StatisticsService, SuggestionEngine
from app.report import ReportGenerator

class BarChart(QWidget):
    def __init__(self,title="",parent=None): super().__init__(parent); self.title=title; self.items=[]; self.setMinimumHeight(230)
    def set_items(self,items): self.items=items; self.update()
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.drawText(12,20,self.title)
        if not self.items: p.drawText(20,55,"暂无数据"); return
        maxv=max((v for _,v in self.items),default=1) or 1; left,bottom,top=45,self.height()-35,40; width=max(1,self.width()-left-20); gap=8; n=min(12,len(self.items)); bw=max(8,(width-gap*n)/max(1,n))
        p.drawLine(left,top,left,bottom); p.drawLine(left,bottom,self.width()-15,bottom)
        for i,(label,val) in enumerate(self.items[:12]):
            x=left+i*(bw+gap); h=(bottom-top)*(val/maxv); p.drawRect(QRectF(x,bottom-h,bw,h)); p.drawText(QRectF(x-10,bottom+3,bw+20,28),Qt.AlignCenter,str(label)); p.drawText(QRectF(x-10,bottom-h-20,bw+20,20),Qt.AlignCenter,f"{val:.0f}")

class LineChart(QWidget):
    def __init__(self,title="",parent=None): super().__init__(parent); self.title=title; self.items=[]; self.setMinimumHeight(230)
    def set_items(self,items): self.items=items; self.update()
    def paintEvent(self,e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.drawText(12,20,self.title)
        if not self.items: p.drawText(20,55,"暂无数据"); return
        left,bottom,top=50,self.height()-35,40; right=self.width()-20; maxv=max((v for _,v in self.items),default=1) or 1; p.drawLine(left,top,left,bottom); p.drawLine(left,bottom,right,bottom)
        pts=[]
        for i,(label,val) in enumerate(self.items):
            x=left+(right-left)*(i/max(1,len(self.items)-1)); y=bottom-(bottom-top)*val/maxv; pts.append((x,y)); p.drawEllipse(QRectF(x-3,y-3,6,6)); p.drawText(QRectF(x-45,bottom+3,90,28),Qt.AlignCenter,str(label)[5:])
        for a,b in zip(pts,pts[1:]): p.drawLine(a[0],a[1],b[0],b[1])

class StatisticsWindow(QMainWindow):
    def __init__(self,statistics_service:StatisticsService,parent=None):
        super().__init__(parent); self.statistics_service=statistics_service; self.engine=SuggestionEngine(statistics_service.database); self.setWindowTitle("剩菜检测系统 - V25 统计分析"); self.resize(1350,900); self._build_ui(); self._load_statistics()
    def _build_ui(self):
        c=QWidget(); root=QVBoxLayout(c); root.setSpacing(10)
        title=QLabel("统计分析与报告"); title.setStyleSheet("font-size:26px;font-weight:bold;"); root.addWidget(title)
        filters=QGroupBox("统计条件"); f=QFormLayout(filters); self.start_date=QDateEdit(calendarPopup=True); self.end_date=QDateEdit(calendarPopup=True); self._set_default_date_range(); f.addRow("开始日期",self.start_date); f.addRow("结束日期",self.end_date); b=QPushButton("查询"); b.clicked.connect(self._load_statistics); r=QPushButton("重置"); r.clicked.connect(self._reset_filters); row=QHBoxLayout(); row.addStretch(); row.addWidget(r); row.addWidget(b); f.addRow(row); root.addWidget(filters)
        summary=QGroupBox("总体统计 / 核心指标"); sl=QHBoxLayout(summary); self.metrics={}
        for key,title in [("events","事件数量"),("initial","初始总重量"),("remaining","总剩余重量"),("consumed","总消耗量"),("rr","平均剩余率"),("cr","平均消耗率")]: self.metrics[key]=self._metric(title); sl.addWidget(self.metrics[key],1)
        root.addWidget(summary)
        export=QGroupBox("报告导出"); er=QHBoxLayout(export); self.export_btn=QPushButton("导出 Excel 统计报告"); self.export_btn.clicked.connect(self._export_excel); self.export_hint=QLabel("包含：统计总览、食物统计、每日统计、自动建议"); er.addWidget(self.export_btn); er.addWidget(self.export_hint); er.addStretch(); root.addWidget(export)
        charts=QSplitter(Qt.Horizontal); self.food_chart=BarChart("按食物统计：各食物总剩余重量（g）"); self.daily_chart=LineChart("按日期统计：每日总剩余重量（g）"); charts.addWidget(self.food_chart); charts.addWidget(self.daily_chart); root.addWidget(charts)
        detail=QSplitter(Qt.Vertical); self.food_table=QTableWidget(0,8); self.food_table.setHorizontalHeaderLabels(["食物","格位数","初始(g)","剩余(g)","消耗(g)","剩余率","消耗率","建议"]); self._style_table(self.food_table); detail.addWidget(self.food_table); self.daily_table=QTableWidget(0,6); self.daily_table.setHorizontalHeaderLabels(["日期","事件","初始(g)","剩余(g)","消耗(g)","剩余率"]); self._style_table(self.daily_table); detail.addWidget(self.daily_table); detail.setSizes([330,220]); root.addWidget(detail,1)
        self.suggestion=QLabel("建议：-"); self.suggestion.setWordWrap(True); self.suggestion.setStyleSheet("font-size:15px;padding:10px;border:1px solid #d9e1e8;background:#f7fbff;"); root.addWidget(self.suggestion); self.setCentralWidget(c)
    def _style_table(self,t):
        t.setEditTriggers(QTableWidget.NoEditTriggers); t.setAlternatingRowColors(True); t.setSelectionBehavior(QTableWidget.SelectRows); t.horizontalHeader().setStretchLastSection(True); t.verticalHeader().setVisible(False); t.setStyleSheet("QHeaderView::section{font-weight:bold;padding:7px;} QTableWidget{gridline-color:#d9e1e8;}")
    def _metric(self,title):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel(title)); v=QLabel("-"); v.setObjectName("metricValue"); v.setStyleSheet("font-size:22px;font-weight:bold;"); l.addWidget(v); return w
    def _set_metric(self,k,v): self.metrics[k].findChild(QLabel,"metricValue").setText(v)
    def _range(self): return datetime.combine(self.start_date.date().toPython(),time.min),datetime.combine(self.end_date.date().toPython(),time.max)
    def _load_statistics(self):
        try:
            start,end=self._range(); self.current_query=StatisticsQuery(start_time=start,end_time=end); s=self.statistics_service.get_summary(self.current_query); fs=self.statistics_service.get_food_statistics(self.current_query); ds=self.statistics_service.get_daily_statistics(self.current_query); self.current_food_stats=fs; self.current_daily_stats=ds; self.current_summary=s
        except Exception as exc: QMessageBox.critical(self,"统计失败",str(exc)); return
        self._set_metric("events",str(s.event_count)); self._set_metric("initial",f"{s.total_initial_weight:.1f} g"); self._set_metric("remaining",f"{s.total_remaining_weight:.1f} g"); self._set_metric("consumed","-" if s.total_consumed_weight is None else f"{s.total_consumed_weight:.1f} g"); self._set_metric("rr","-" if s.remaining_rate is None else f"{s.remaining_rate:.1%}"); self._set_metric("cr","-" if s.consumption_rate is None else f"{s.consumption_rate:.1%}")
        self.food_chart.set_items([(x.food_name,x.total_remaining_weight) for x in fs]); self.daily_chart.set_items([(x.date,x.total_remaining_weight) for x in ds])
        self.food_table.setRowCount(0); suggestions=[]
        for x in fs:
            row=self.food_table.rowCount(); self.food_table.insertRow(row); sg=self.engine.match(x.remaining_rate); suggestions.extend(f"{x.food_name}：{z}" for z in sg); vals=[x.food_name,str(x.count),f"{x.total_initial_weight:.1f}",f"{x.total_remaining_weight:.1f}","-" if x.total_consumed_weight is None else f"{x.total_consumed_weight:.1f}","-" if x.remaining_rate is None else f"{x.remaining_rate:.1%}","-" if x.consumption_rate is None else f"{x.consumption_rate:.1%}","；".join(sg) or "-"]; [self.food_table.setItem(row,i,QTableWidgetItem(v)) for i,v in enumerate(vals)]
        self.daily_table.setRowCount(0)
        for x in ds:
            row=self.daily_table.rowCount(); self.daily_table.insertRow(row); vals=[x.date,str(x.event_count),f"{x.total_initial_weight:.1f}",f"{x.total_remaining_weight:.1f}","-" if x.total_consumed_weight is None else f"{x.total_consumed_weight:.1f}","-" if x.remaining_rate is None else f"{x.remaining_rate:.1%}"]; [self.daily_table.setItem(row,i,QTableWidgetItem(v)) for i,v in enumerate(vals)]
        self.suggestion.setText("建议："+("；".join(suggestions[:8]) if suggestions else "当前数据未命中配置规则。"))
    def _export_excel(self):
        if not hasattr(self,"current_query"): return
        default=str((self.statistics_service.database.path.parent if hasattr(self.statistics_service.database,'path') else Path('.')) / "剩菜统计报告.xlsx")
        path,_=QFileDialog.getSaveFileName(self,"导出 Excel 统计报告",default,"Excel 文件 (*.xlsx)")
        if not path: return
        try:
            fs=self.current_food_stats; suggestions=[]
            for x in fs:
                suggestions.extend(f"{x.food_name}：{z}" for z in self.engine.match(x.remaining_rate))
            out=ReportGenerator(Path(path).parent).generate_statistics_xlsx(self.statistics_service,self.current_query,suggestions,Path(path))
            self.export_hint.setText(f"已导出：{out}"); QMessageBox.information(self,"导出成功",f"统计报告已导出：\n{out}")
        except Exception as exc: QMessageBox.critical(self,"导出失败",str(exc))
    def _set_default_date_range(self): today=self.end_date.date().currentDate(); self.start_date.setDate(today.addDays(-30)); self.end_date.setDate(today)
    def _reset_filters(self): self._set_default_date_range(); self._load_statistics()
