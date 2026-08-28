import { useState } from "react";
import { Plus, Cpu, Loader2 } from "lucide-react";
import { api, Equipment } from "../lib/api";

interface Props {
  equipment: Equipment[];
  onCreated: () => void;
}

export default function EquipmentManager({ equipment, onCreated }: Props) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ manufacturer: "", model: "", equipment_type: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (!form.manufacturer.trim() || !form.model.trim() || !form.equipment_type.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await api.equipment.create(form);
      setForm({ manufacturer: "", model: "", equipment_type: "" });
      setShowForm(false);
      onCreated();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3">
      {equipment.map((eq) => (
        <div key={eq.id} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5 border border-white/8">
          <Cpu className="w-4 h-4 text-forge-accent flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-white">{eq.manufacturer} {eq.model}</p>
            <p className="text-[10px] text-forge-muted">{eq.equipment_type}</p>
          </div>
        </div>
      ))}

      {showForm ? (
        <div className="space-y-2 p-3 rounded-lg border border-white/15 bg-white/5">
          {["manufacturer", "model", "equipment_type"].map((field) => (
            <input
              key={field}
              value={(form as any)[field]}
              onChange={(e) => setForm((p) => ({ ...p, [field]: e.target.value }))}
              placeholder={field.replace("_", " ")}
              className="w-full bg-forge-navy border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-forge-muted focus:outline-none focus:border-forge-accent"
            />
          ))}
          {error && <p className="text-xs text-red-400">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={save}
              disabled={saving}
              className="flex-1 py-1.5 rounded-lg bg-forge-accent text-white text-xs font-medium hover:bg-orange-600 disabled:opacity-50 transition-colors flex items-center justify-center gap-1"
            >
              {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : "Save"}
            </button>
            <button
              onClick={() => { setShowForm(false); setError(null); }}
              className="flex-1 py-1.5 rounded-lg border border-white/10 text-white/60 text-xs hover:border-white/30 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowForm(true)}
          className="w-full flex items-center justify-center gap-1.5 py-2 rounded-lg border border-dashed border-white/20 text-xs text-forge-muted hover:border-forge-accent hover:text-forge-accent transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Add equipment
        </button>
      )}
    </div>
  );
}
