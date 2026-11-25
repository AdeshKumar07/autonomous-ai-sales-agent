import {
  Briefcase,
  Building2,
  CalendarClock,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Flame,
  IndianRupee,
  User,
} from "lucide-react";
import { useState } from "react";

const STATUS_STYLES = {
  HOT: "border-rose-200 bg-rose-50 text-rose-700",
  WARM: "border-amber-200 bg-amber-50 text-amber-700",
  COLD: "border-sky-200 bg-sky-50 text-sky-700",
  NEW: "border-slate-200 bg-slate-100 text-slate-700",
};

function LeadField({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-2.5 rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">
          {label}
        </p>
        <p className="mt-0.5 break-words text-xs font-medium text-slate-800">
          {value || <span className="font-normal text-slate-400">Not captured yet</span>}
        </p>
      </div>
    </div>
  );
}

function LeadPanel({ lead }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const status = (lead?.qualification_status || "NEW").toUpperCase();
  const badgeStyle = STATUS_STYLES[status] || STATUS_STYLES.NEW;

  return (
    <aside className="border-t border-slate-200 bg-white lg:w-80 lg:shrink-0 lg:border-t-0 lg:border-l lg:overflow-y-auto">
      {/* Mobile toggle header */}
      <button
        type="button"
        onClick={() => setMobileOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-4 py-2.5 text-left lg:hidden"
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-800">Lead Profile</span>
          <span
            className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold ${badgeStyle}`}
          >
            {status}
          </span>
        </div>
        {mobileOpen ? (
          <ChevronUp className="h-4 w-4 text-slate-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-500" />
        )}
      </button>

      {/* Panel content */}
      <div className={`${mobileOpen ? "block" : "hidden"} px-4 pb-4 lg:block lg:p-5`}>
        <div className="hidden items-center justify-between lg:flex">
          <h2 className="text-sm font-semibold text-slate-900">Lead Information</h2>
          <span
            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${badgeStyle}`}
          >
            {status}
          </span>
        </div>

        <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:mt-4 lg:grid-cols-1">
          <LeadField icon={User} label="Customer Name" value={lead?.customer_name} />
          <LeadField icon={Building2} label="Company" value={lead?.company_name} />
          <LeadField
            icon={ClipboardList}
            label="Business Requirements"
            value={lead?.requirements}
          />
          <LeadField icon={IndianRupee} label="Budget" value={lead?.budget} />
          <LeadField
            icon={CalendarClock}
            label="Purchase Timeline"
            value={lead?.purchase_timeline}
          />
          <LeadField icon={Flame} label="Interest Level" value={lead?.interest_level} />
          {lead?.business_type && (
            <LeadField icon={Briefcase} label="Business Type" value={lead.business_type} />
          )}
        </div>

        {lead?.qualification_reason && (
          <div className="mt-3 rounded-xl border border-indigo-100 bg-indigo-50/60 px-3 py-2.5">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-indigo-700">
              Qualification Reason
            </p>
            <p className="mt-1 text-xs leading-relaxed text-indigo-900">
              {lead.qualification_reason}
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}

export default LeadPanel;
