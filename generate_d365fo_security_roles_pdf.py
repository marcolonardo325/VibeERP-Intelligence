"""
Generate a PDF document mapping D365 F&O Security Roles → Duties → License Types.
Covers Finance, Supply Chain Management, Commerce, Human Resources, and Project Operations.
"""

from fpdf import FPDF
import os
from datetime import date

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "D365FO_Security_Roles_Duties_Licenses.pdf")


# ─────────────────────────────────────────────────────────────────────────────
# DATA: Security Roles → Duties → License Type
# ─────────────────────────────────────────────────────────────────────────────

LICENSE_DESCRIPTIONS = {
    "Finance": "Full user license for Dynamics 365 Finance. Grants access to general ledger, accounts payable/receivable, budgeting, fixed assets, cash management, and financial reporting.",
    "Supply Chain Management": "Full user license for Dynamics 365 Supply Chain Management. Grants access to procurement, inventory, warehouse, production, transportation, and quality management.",
    "Commerce": "Full user license for Dynamics 365 Commerce. Grants access to retail channel management, merchandising, POS, e-commerce, call center, and unified pricing.",
    "Human Resources": "Full user license for Dynamics 365 Human Resources. Grants access to workforce management, leave/absence, benefits, compensation, training, and compliance.",
    "Project Operations": "Full user license for Dynamics 365 Project Operations. Grants access to project planning, resource management, time/expense, project accounting, and billing.",
    "Team Members": "Limited user license for light-touch scenarios: self-service HR, time/expense entry, approvals, read-only dashboards. Cannot perform full transactional operations.",
    "Activity": "Task-specific user license for repetitive operational tasks: warehouse mobile device operations, shop floor execution, production floor input. Very limited menu access.",
    "Device": "Shared device license allowing multiple workers to use a single shared device (e.g. warehouse scanner, kiosk). Not tied to a named user.",
}

# Each entry: (Role Name, Role AOT Name, License, [list of (Duty Name, Duty AOT Name)])
ROLES_DATA = [
    # ═══════════════════════════════════════════════════════════════════════
    # FINANCE
    # ═══════════════════════════════════════════════════════════════════════
    ("System Administrator", "SystemAdministrator", "Finance",
     [("System administration maintain", "SysServerConfigMaintain"),
      ("Security privilege maintain", "SysSecurityPrivilegeMaintain"),
      ("Batch job maintain", "SysBatchJobMaintain"),
      ("Number sequence maintain", "NumberSequenceReferenceMaintain"),
      ("Electronic reporting manage", "ERFormatMappingRunByRoleAdmin")]),

    ("Chief Financial Officer", "CFO", "Finance",
     [("Financial statement inquire", "LedgerFinancialStatementInquire"),
      ("Budget overview inquire", "BudgetPlanInquire"),
      ("Cash flow overview inquire", "LedgerCashInflowOutflowInquire"),
      ("Financial period close manage", "LedgerPeriodCloseWorkspaceMaintain"),
      ("Audit policy maintain", "AuditPolicyMaintain"),
      ("Intercompany accounting maintain", "LedgerInterCompanyMaintain")]),

    ("Financial Controller", "FinancialController", "Finance",
     [("General ledger daily journal maintain", "LedgerJournalMaintain"),
      ("Chart of accounts maintain", "MainAccountMaintain"),
      ("Financial dimension maintain", "DimensionValueMaintain"),
      ("Ledger allocation rules maintain", "LedgerAllocationRulesMaintain"),
      ("Consolidation maintain", "LedgerConsolidationMaintain"),
      ("Journal approval maintain", "LedgerJournalApprovalMaintain"),
      ("Financial period close maintain", "LedgerPeriodCloseMaintain")]),

    ("Accounting Manager", "AccountingManager", "Finance",
     [("General journal maintain", "LedgerJournalMaintain"),
      ("Chart of accounts maintain", "MainAccountMaintain"),
      ("Posting profiles maintain", "CustPostingProfileMaintain"),
      ("Subledger journal entry inquire", "SubledgerJournalEntryInquire"),
      ("Ledger accrual schemes maintain", "LedgerAccrualSchemesMaintain"),
      ("Financial period close process", "LedgerPeriodCloseProcess")]),

    ("Accounting Supervisor", "AccountingSupervisor", "Finance",
     [("General journal maintain", "LedgerJournalMaintain"),
      ("Ledger journal approve", "LedgerJournalApprove"),
      ("Subledger journal transfer review", "SubledgerJournalTransferReview"),
      ("Bank reconciliation maintain", "BankReconciliationMaintain"),
      ("Period close journal maintain", "LedgerPeriodCloseJournalMaintain")]),

    ("Accounts Payable Manager", "AccountsPayableManager", "Finance",
     [("Vendor invoice maintain", "VendInvoiceJournalMaintain"),
      ("Vendor payment journal maintain", "LedgerJournalVendPaymentMaintain"),
      ("Vendor master maintain", "VendTableMaintain"),
      ("Vendor settlement maintain", "VendSettlementMaintain"),
      ("Vendor aging inquiry", "VendAgingInquire"),
      ("Purchase invoice matching maintain", "VendInvoiceMatchingMaintain"),
      ("Vendor hold manage", "VendOnHoldMaintain")]),

    ("Accounts Payable Clerk", "AccountsPayableClerk", "Finance",
     [("Vendor invoice entry maintain", "VendInvoiceJournalEntryMaintain"),
      ("Vendor invoice register maintain", "VendInvoiceRegisterMaintain"),
      ("Vendor payment proposal maintain", "VendPaymentProposalMaintain"),
      ("Vendor transaction inquire", "VendTransInquire"),
      ("Vendor invoice approval maintain", "VendInvoiceApprovalJournalMaintain")]),

    ("Accounts Receivable Manager", "AccountsReceivableManager", "Finance",
     [("Customer invoice maintain", "CustInvoiceJournalMaintain"),
      ("Customer payment journal maintain", "CustPaymentJournalMaintain"),
      ("Customer master maintain", "CustTableMaintain"),
      ("Customer settlement maintain", "CustSettlementMaintain"),
      ("Customer credit limit maintain", "CustCreditLimitMaintain"),
      ("Collections manage", "CollectionLetterMaintain"),
      ("Customer aging inquiry", "CustAgingInquire")]),

    ("Accounts Receivable Clerk", "AccountsReceivableClerk", "Finance",
     [("Customer payment entry maintain", "CustPaymentJournalEntryMaintain"),
      ("Free text invoice maintain", "FreeTextInvoiceMaintain"),
      ("Customer transaction inquire", "CustTransInquire"),
      ("Customer balance inquire", "CustBalanceInquire"),
      ("Interest notes maintain", "InterestNoteMaintain")]),

    ("Budget Manager", "BudgetManager", "Finance",
     [("Budget maintain", "BudgetMaintain"),
      ("Budget plan maintain", "BudgetPlanMaintain"),
      ("Budget register entry maintain", "BudgetRegisterEntryMaintain"),
      ("Budget transfer rules maintain", "BudgetTransferRulesMaintain"),
      ("Budget control configure", "BudgetControlConfigureMaintain"),
      ("Budget allocation maintain", "BudgetAllocationMaintain")]),

    ("Budget Clerk", "BudgetClerk", "Finance",
     [("Budget register entry maintain", "BudgetRegisterEntryMaintain"),
      ("Budget plan entry maintain", "BudgetPlanEntryMaintain"),
      ("Budget inquire", "BudgetInquire"),
      ("Budget transfer maintain", "BudgetTransferMaintain")]),

    ("Collections Agent", "CollectionsAgent", "Finance",
     [("Collections activities maintain", "CollectionActivitiesMaintain"),
      ("Customer aging inquire", "CustAgingInquire"),
      ("Collection letter maintain", "CollectionLetterMaintain"),
      ("Customer write-off maintain", "CustWriteOffMaintain"),
      ("Customer promise to pay maintain", "CustPromissoryNoteMaintain")]),

    ("Treasurer", "Treasurer", "Finance",
     [("Bank management maintain", "BankManagementMaintain"),
      ("Cash and bank management", "CashBankManagementMaintain"),
      ("Bank reconciliation maintain", "BankReconciliationMaintain"),
      ("Cash flow forecast maintain", "CashFlowForecastMaintain"),
      ("Letter of credit maintain", "LetterOfCreditMaintain"),
      ("Foreign currency revaluation maintain", "LedgerForeignCurrencyRevalMaintain")]),

    ("Fixed Assets Accountant", "FixedAssetsAccountant", "Finance",
     [("Fixed assets maintain", "AssetMaintain"),
      ("Fixed assets depreciation maintain", "AssetDepreciationMaintain"),
      ("Fixed assets acquisition maintain", "AssetAcquisitionMaintain"),
      ("Fixed assets disposal maintain", "AssetDisposalMaintain"),
      ("Fixed assets journal maintain", "AssetJournalMaintain"),
      ("Fixed assets inquiry", "AssetInquire")]),

    ("Tax Accountant", "TaxAccountant", "Finance",
     [("Sales tax maintain", "TaxSalesTaxMaintain"),
      ("Sales tax payment maintain", "TaxSalesTaxPaymentMaintain"),
      ("Tax report inquire", "TaxReportInquire"),
      ("Tax configuration maintain", "TaxConfigurationMaintain"),
      ("Withholding tax maintain", "TaxWithholdingMaintain")]),

    ("Cost Accountant", "CostAccountant", "Finance",
     [("Cost accounting maintain", "CostAccountingMaintain"),
      ("Cost element maintain", "CostElementMaintain"),
      ("Cost behavior maintain", "CostBehaviorMaintain"),
      ("Cost distribution maintain", "CostDistributionMaintain"),
      ("Cost ledger inquire", "CostLedgerInquire")]),

    # ═══════════════════════════════════════════════════════════════════════
    # SUPPLY CHAIN MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    ("Purchasing Manager", "PurchasingManager", "Supply Chain Management",
     [("Purchase order maintain", "PurchOrderMaintain"),
      ("Purchase requisition approve", "PurchReqApprove"),
      ("Vendor master maintain", "VendTableMaintain"),
      ("Purchase agreement maintain", "PurchAgreementMaintain"),
      ("Purchasing policy maintain", "PurchPolicyMaintain"),
      ("Request for quotation maintain", "PurchRFQMaintain"),
      ("Category hierarchy maintain", "ProcCategoryHierarchyMaintain")]),

    ("Purchasing Agent", "PurchasingAgent", "Supply Chain Management",
     [("Purchase order entry maintain", "PurchOrderEntryMaintain"),
      ("Purchase order confirmation maintain", "PurchOrderConfirmMaintain"),
      ("Product receipt maintain", "PurchPackingSlipMaintain"),
      ("Request for quotation manage", "PurchRFQManage"),
      ("Purchase requisition review", "PurchReqReview"),
      ("Vendor inquiry", "VendTableInquire")]),

    ("Inventory Manager", "InventoryManager", "Supply Chain Management",
     [("Inventory journal maintain", "InventJournalMaintain"),
      ("Inventory counting maintain", "InventCountingMaintain"),
      ("Inventory adjustment maintain", "InventAdjustmentMaintain"),
      ("Inventory transfer maintain", "InventTransferMaintain"),
      ("Inventory blocking maintain", "InventBlockingMaintain"),
      ("Inventory dimensions setup", "InventDimensionSetupMaintain"),
      ("Item master maintain", "EcoResProductMaintain")]),

    ("Warehouse Manager", "WarehouseManager", "Supply Chain Management",
     [("Warehouse management setup maintain", "WHSSetupMaintain"),
      ("Wave processing maintain", "WHSWaveProcessingMaintain"),
      ("Location directive maintain", "WHSLocationDirectiveMaintain"),
      ("Work template maintain", "WHSWorkTemplateMaintain"),
      ("Warehouse operations monitor", "WHSWarehouseOperationsMonitor"),
      ("Load planning maintain", "WHSLoadPlanningMaintain"),
      ("Cycle counting maintain", "WHSCycleCountingMaintain")]),

    ("Production Manager", "ProductionManager", "Supply Chain Management",
     [("Production order maintain", "ProdOrderMaintain"),
      ("Production scheduling maintain", "ProdSchedulingMaintain"),
      ("BOM management maintain", "BOMMaintain"),
      ("Route management maintain", "RouteMaintain"),
      ("Production control monitor", "ProdControlMonitor"),
      ("Batch order maintain", "PmfBatchOrderMaintain")]),

    ("Production Planner", "ProductionPlanner", "Supply Chain Management",
     [("Master planning maintain", "ReqPlanMaintain"),
      ("Planned order firming maintain", "ReqPlannedOrderFirmingMaintain"),
      ("Production schedule maintain", "ProdScheduleMaintain"),
      ("Material requirements planning run", "ReqMRPRunProcess"),
      ("Supply forecast maintain", "ForecastSupplyMaintain"),
      ("Demand forecast maintain", "ForecastDemandMaintain")]),

    ("Quality Manager", "QualityManager", "Supply Chain Management",
     [("Quality order maintain", "InventQualityOrderMaintain"),
      ("Quality test maintain", "InventQualityTestMaintain"),
      ("Non-conformance maintain", "InventNonConformanceMaintain"),
      ("Quality association maintain", "InventQualityAssociationMaintain"),
      ("Certificate of analysis maintain", "InventCertOfAnalysisMaintain")]),

    ("Shipping Clerk", "ShippingClerk", "Supply Chain Management",
     [("Sales packing slip maintain", "SalesPackingSlipMaintain"),
      ("Shipment maintain", "WHSShipmentMaintain"),
      ("Transportation management maintain", "TMSTransportationMaintain"),
      ("Delivery schedule maintain", "SalesDeliveryScheduleMaintain"),
      ("Bill of lading maintain", "TMSBillOfLadingMaintain")]),

    ("Receiving Clerk", "ReceivingClerk", "Supply Chain Management",
     [("Product receipt entry maintain", "PurchPackingSlipEntryMaintain"),
      ("Arrival overview manage", "InventArrivalOverviewManage"),
      ("Item arrival journal maintain", "InventItemArrivalJournalMaintain"),
      ("Return order receive", "ReturnOrderReceiveMaintain"),
      ("Quality order entry maintain", "InventQualityOrderEntryMaintain")]),

    ("Transportation Coordinator", "TransportationCoordinator", "Supply Chain Management",
     [("Load management maintain", "TMSLoadMaintain"),
      ("Freight reconciliation maintain", "TMSFreightReconciliationMaintain"),
      ("Rate route maintain", "TMSRateRouteMaintain"),
      ("Carrier management maintain", "TMSCarrierMaintain"),
      ("Transportation tender maintain", "TMSTenderMaintain")]),

    # ═══════════════════════════════════════════════════════════════════════
    # SALES
    # ═══════════════════════════════════════════════════════════════════════
    ("Sales Manager", "SalesManager", "Supply Chain Management",
     [("Sales order maintain", "SalesOrderMaintain"),
      ("Sales quotation maintain", "SalesQuotationMaintain"),
      ("Sales agreement maintain", "SalesAgreementMaintain"),
      ("Sales pricing maintain", "SalesPriceMaintain"),
      ("Customer master maintain", "CustTableMaintain"),
      ("Commission maintain", "CommissionMaintain"),
      ("Sales performance inquire", "SalesPerformanceInquire")]),

    ("Sales Clerk", "SalesClerk", "Supply Chain Management",
     [("Sales order entry maintain", "SalesOrderEntryMaintain"),
      ("Sales quotation entry maintain", "SalesQuotationEntryMaintain"),
      ("Sales packing slip maintain", "SalesPackingSlipMaintain"),
      ("Customer inquire", "CustTableInquire"),
      ("Sales order confirmation maintain", "SalesOrderConfirmMaintain")]),

    # ═══════════════════════════════════════════════════════════════════════
    # COMMERCE
    # ═══════════════════════════════════════════════════════════════════════
    ("Retail Operations Manager", "RetailOperationsManager", "Commerce",
     [("Channel management maintain", "RetailChannelMaintain"),
      ("Product assortment maintain", "RetailAssortmentMaintain"),
      ("Retail pricing maintain", "RetailPriceMaintain"),
      ("Retail discount maintain", "RetailDiscountMaintain"),
      ("POS operations maintain", "RetailPOSOperationsMaintain"),
      ("Statement maintain", "RetailStatementMaintain"),
      ("Unified pricing management", "GUPPricingMaintain")]),

    ("Retail Merchandising Manager", "RetailMerchandisingManager", "Commerce",
     [("Product catalog maintain", "RetailCatalogMaintain"),
      ("Category hierarchy maintain", "EcoResCategoryHierarchyMaintain"),
      ("Product attribute maintain", "EcoResProductAttributeMaintain"),
      ("Retail product management", "RetailProductManagementMaintain"),
      ("Price adjustment maintain", "RetailPriceAdjustmentMaintain")]),

    ("Store Manager", "RetailStoreManager", "Commerce",
     [("Store operations maintain", "RetailStoreOperationsMaintain"),
      ("POS register maintain", "RetailTerminalMaintain"),
      ("Cash management maintain", "RetailCashManagementMaintain"),
      ("Staff management maintain", "RetailStaffMaintain"),
      ("Inventory lookup inquire", "RetailInventoryLookupInquire")]),

    # ═══════════════════════════════════════════════════════════════════════
    # HUMAN RESOURCES
    # ═══════════════════════════════════════════════════════════════════════
    ("Human Resources Manager", "HumanResourcesManager", "Human Resources",
     [("Worker maintain", "HcmWorkerMaintain"),
      ("Position maintain", "HcmPositionMaintain"),
      ("Department maintain", "HcmDepartmentMaintain"),
      ("Compensation plan maintain", "HcmCompensationMaintain"),
      ("Benefits administration maintain", "HcmBenefitMaintain"),
      ("Leave and absence manage", "HcmLeaveAbsenceMaintain"),
      ("Personnel actions maintain", "HcmPersonnelActionMaintain")]),

    ("Compensation and Benefits Manager", "CompensationBenefitsManager", "Human Resources",
     [("Compensation plan maintain", "HcmCompensationPlanMaintain"),
      ("Fixed compensation maintain", "HcmFixedCompensationMaintain"),
      ("Variable compensation maintain", "HcmVariableCompensationMaintain"),
      ("Benefits eligibility maintain", "HcmBenefitEligibilityMaintain"),
      ("Benefits enrollment maintain", "HcmBenefitEnrollmentMaintain"),
      ("Payroll maintain", "PayrollMaintain")]),

    ("Recruiter", "HcmRecruiter", "Human Resources",
     [("Recruiting maintain", "HcmRecruitingMaintain"),
      ("Job application maintain", "HcmApplicationMaintain"),
      ("Job posting maintain", "HcmJobPostingMaintain"),
      ("Interview scheduling maintain", "HcmInterviewMaintain"),
      ("Applicant inquiry", "HcmApplicantInquire")]),

    ("Training Manager", "TrainingManager", "Human Resources",
     [("Course maintain", "HcmCourseMaintain"),
      ("Skills management maintain", "HcmSkillsMaintain"),
      ("Certificate maintain", "HcmCertificateMaintain"),
      ("Performance review maintain", "HcmPerformanceReviewMaintain"),
      ("Competency maintain", "HcmCompetencyMaintain")]),

    # ═══════════════════════════════════════════════════════════════════════
    # PROJECT OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════
    ("Project Manager", "ProjectManager", "Project Operations",
     [("Project maintain", "ProjProjectMaintain"),
      ("Project budget maintain", "ProjBudgetMaintain"),
      ("WBS maintain", "ProjWBSMaintain"),
      ("Project resource scheduling maintain", "ProjResourceSchedulingMaintain"),
      ("Project invoice proposal maintain", "ProjInvoiceProposalMaintain"),
      ("Project estimate maintain", "ProjEstimateMaintain")]),

    ("Project Accountant", "ProjectAccountant", "Project Operations",
     [("Project transaction maintain", "ProjTransactionMaintain"),
      ("Project adjustment maintain", "ProjAdjustmentMaintain"),
      ("Project revenue recognition maintain", "ProjRevenueRecognitionMaintain"),
      ("Project WIP maintain", "ProjWIPMaintain"),
      ("Project elimination maintain", "ProjEliminationMaintain"),
      ("Project cost control inquire", "ProjCostControlInquire")]),

    # ═══════════════════════════════════════════════════════════════════════
    # TEAM MEMBERS (LIMITED)
    # ═══════════════════════════════════════════════════════════════════════
    ("Employee Self-Service", "EmployeeSelfService", "Team Members",
     [("Personal information maintain (self)", "HcmPersonalInfoSelfMaintain"),
      ("Leave request entry maintain", "HcmLeaveRequestMaintain"),
      ("Expense report entry maintain", "TrvExpenseReportSelfMaintain"),
      ("Time entry maintain (self)", "ProjTimesheetSelfEntryMaintain"),
      ("Benefits enrollment (self)", "HcmBenefitSelfEnrollMaintain"),
      ("Approved vendor list inquire", "VendApprovedListInquire")]),

    ("Manager Self-Service", "ManagerSelfService", "Team Members",
     [("Team member inquire", "HcmTeamMemberInquire"),
      ("Leave request approve", "HcmLeaveRequestApprove"),
      ("Expense report approve", "TrvExpenseReportApprove"),
      ("Timesheet approve", "ProjTimesheetApprove"),
      ("Position request maintain", "HcmPositionRequestMaintain"),
      ("Performance goal manage", "HcmPerformanceGoalManage")]),

    ("Vendor Collaboration", "VendorCollaboration", "Team Members",
     [("Vendor collaboration invoice maintain", "VendCollaborationInvoiceMaintain"),
      ("Vendor collaboration PO inquiry", "VendCollaborationPOInquire"),
      ("Vendor collaboration RFQ respond", "VendCollaborationRFQRespond"),
      ("Vendor profile maintain (self)", "VendProfileSelfMaintain")]),

    # ═══════════════════════════════════════════════════════════════════════
    # ACTIVITY (TASK USERS)
    # ═══════════════════════════════════════════════════════════════════════
    ("Warehouse Mobile Device User", "WarehouseMobileDeviceUser", "Activity",
     [("Warehouse mobile device operate", "WHSMobileDeviceOperate"),
      ("Inbound operations mobile", "WHSInboundMobileOperate"),
      ("Outbound operations mobile", "WHSOutboundMobileOperate"),
      ("Cycle counting mobile", "WHSCycleCountMobileOperate"),
      ("Inventory movement mobile", "WHSInventMovementMobileOperate")]),

    ("Production Floor Operator", "ProductionFloorOperator", "Activity",
     [("Job card terminal operate", "JmgJobCardTerminalOperate"),
      ("Production reporting operate", "ProdReportingOperate"),
      ("Material consumption reporting", "ProdMaterialConsumptionReport"),
      ("Route card journal maintain", "ProdRouteCardJournalMaintain")]),

    ("Shop Floor Supervisor", "ShopFloorSupervisor", "Activity",
     [("Production overview monitor", "ProdOverviewMonitor"),
      ("Shop floor execution maintain", "ProdShopFloorExecutionMaintain"),
      ("Time attendance approve", "JmgTimeAttendanceApprove"),
      ("Production order report as finished", "ProdReportFinishedOperate")]),
]


# ─────────────────────────────────────────────────────────────────────────────
# PDF Generation
# ─────────────────────────────────────────────────────────────────────────────

class SecurityRolesPDF(FPDF):
    """Custom PDF class with header/footer and helper methods."""

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Dynamics 365 Finance & Operations - Security Roles, Duties & License Mapping", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_draw_color(0, 120, 212)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}  |  Generated {date.today().isoformat()}  |  Reference document - verify against your environment", align="C")

    def section_title(self, title):
        """Print a colored section header."""
        self.set_font("Helvetica", "B", 14)
        self.set_fill_color(0, 120, 212)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, f"  {title}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)

    def license_box(self, name, description):
        """Print a license description box."""
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 90, 158)
        self.cell(0, 7, name, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5, description)
        self.ln(2)

    def role_header(self, role_name, aot_name, license_type):
        """Print role name bar."""
        # Check for page break
        if self.get_y() > self.h - 50:
            self.add_page()

        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(235, 245, 255)
        self.set_text_color(0, 60, 120)
        self.cell(0, 8, f"  {role_name}", new_x="LMARGIN", new_y="NEXT", fill=True)

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(95, 5, f"    AOT Name: {aot_name}")
        self.set_font("Helvetica", "B", 8)
        license_colors = {
            "Finance": (0, 120, 60),
            "Supply Chain Management": (180, 100, 0),
            "Commerce": (140, 0, 140),
            "Human Resources": (0, 100, 180),
            "Project Operations": (180, 60, 0),
            "Team Members": (100, 100, 100),
            "Activity": (70, 130, 70),
            "Device": (120, 120, 120),
        }
        r, g, b = license_colors.get(license_type, (0, 0, 0))
        self.set_text_color(r, g, b)
        self.cell(0, 5, f"License: {license_type}", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def duties_table(self, duties):
        """Print duties table for a role."""
        # Table header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(220, 230, 245)
        self.set_text_color(40, 40, 40)
        self.set_draw_color(180, 180, 180)
        self.cell(95, 6, "  Duty Name", border=1, fill=True)
        self.cell(90, 6, "  AOT Identifier", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        # Table rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(50, 50, 50)
        for i, (duty_name, duty_aot) in enumerate(duties):
            if self.get_y() > self.h - 25:
                self.add_page()
                # Reprint header on new page
                self.set_font("Helvetica", "B", 8)
                self.set_fill_color(220, 230, 245)
                self.set_text_color(40, 40, 40)
                self.cell(95, 6, "  Duty Name (cont.)", border=1, fill=True)
                self.cell(90, 6, "  AOT Identifier", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 8)
                self.set_text_color(50, 50, 50)

            fill = i % 2 == 0
            if fill:
                self.set_fill_color(248, 250, 255)
            self.cell(95, 5, f"  {duty_name}", border="LR", fill=fill)
            self.cell(90, 5, f"  {duty_aot}", border="LR", fill=fill, new_x="LMARGIN", new_y="NEXT")

        # Bottom border
        self.cell(185, 0, "", border="T")
        self.ln(4)


def generate_pdf():
    pdf = SecurityRolesPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── COVER PAGE ──
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(0, 120, 212)
    pdf.cell(0, 15, "Dynamics 365", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 12, "Finance & Operations", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)
    pdf.set_draw_color(0, 120, 212)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), pdf.w - 60, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Security Roles, Duties &", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 10, "License Mapping Reference", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, f"Generated: {date.today().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 8, "Based on Dynamics 365 F&O standard security framework", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(20)

    # Disclaimer
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(160, 80, 80)
    pdf.multi_cell(0, 5,
        "DISCLAIMER: This document provides a representative mapping of standard D365 F&O security roles, "
        "duties, and license types. Actual role/duty assignments may vary based on your environment configuration, "
        "customizations, and Microsoft licensing updates. Always verify against your specific Dynamics 365 LCS "
        "subscription and the Security configuration form in your environment.",
        align="C")

    # ── LICENSE OVERVIEW ──
    pdf.add_page()
    pdf.section_title("License Types Overview")
    pdf.ln(2)
    for lic_name, lic_desc in LICENSE_DESCRIPTIONS.items():
        pdf.license_box(lic_name, lic_desc)

    # ── ROLES BY LICENSE CATEGORY ──
    license_order = [
        "Finance",
        "Supply Chain Management",
        "Commerce",
        "Human Resources",
        "Project Operations",
        "Team Members",
        "Activity",
    ]

    for lic in license_order:
        roles_in_lic = [(r, a, l, d) for r, a, l, d in ROLES_DATA if l == lic]
        if not roles_in_lic:
            continue

        pdf.add_page()
        pdf.section_title(f"{lic} - Security Roles & Duties")
        pdf.ln(2)

        for role_name, aot_name, license_type, duties in roles_in_lic:
            pdf.role_header(role_name, aot_name, license_type)
            pdf.duties_table(duties)

    # ── SUMMARY TABLE ──
    pdf.add_page()
    pdf.section_title("Quick Reference: All Roles Summary")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(0, 120, 212)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(180, 180, 180)
    pdf.cell(10, 6, "  #", border=1, fill=True)
    pdf.cell(65, 6, "  Security Role", border=1, fill=True)
    pdf.cell(55, 6, "  License Type", border=1, fill=True)
    pdf.cell(15, 6, "Duties", border=1, fill=True, align="C")
    pdf.cell(45, 6, "  AOT Name", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 7.5)
    for idx, (role_name, aot_name, license_type, duties) in enumerate(ROLES_DATA, 1):
        if pdf.get_y() > pdf.h - 20:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(0, 120, 212)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(10, 6, "  #", border=1, fill=True)
            pdf.cell(65, 6, "  Security Role", border=1, fill=True)
            pdf.cell(55, 6, "  License Type", border=1, fill=True)
            pdf.cell(15, 6, "Duties", border=1, fill=True, align="C")
            pdf.cell(45, 6, "  AOT Name", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 7.5)

        fill = idx % 2 == 0
        if fill:
            pdf.set_fill_color(245, 248, 255)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(10, 5, f"  {idx}", border="LR", fill=fill)
        pdf.cell(65, 5, f"  {role_name}", border="LR", fill=fill)
        pdf.cell(55, 5, f"  {license_type}", border="LR", fill=fill)
        pdf.cell(15, 5, f"{len(duties)}", border="LR", fill=fill, align="C")
        # Truncate aot_name if too long
        disp_aot = aot_name if len(aot_name) <= 28 else aot_name[:25] + "..."
        pdf.cell(45, 5, f"  {disp_aot}", border="LR", fill=fill, new_x="LMARGIN", new_y="NEXT")

    pdf.cell(190, 0, "", border="T")

    # ── Save ──
    pdf.output(OUTPUT_PATH)
    print(f"\nPDF generated successfully: {OUTPUT_PATH}")
    print(f"  Total roles documented: {len(ROLES_DATA)}")
    total_duties = sum(len(d) for _, _, _, d in ROLES_DATA)
    print(f"  Total duties mapped:    {total_duties}")


if __name__ == "__main__":
    generate_pdf()
