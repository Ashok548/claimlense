"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Calendar, Copy, Loader2, Plus, Power, TicketPercent } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type PromoCodeRecord = {
  id: string;
  code: string;
  creditsValue: number;
  maxUses: number;
  usedCount: number;
  expiresAt: string | null;
  isActive: boolean;
  createdAt: string;
  _count?: { redemptions: number };
};

type Message = {
  type: "success" | "error";
  text: string;
};

export function PromoCodeManager({ initialPromoCodes }: { initialPromoCodes: PromoCodeRecord[] }) {
  const router = useRouter();
  const [promoCodes, setPromoCodes] = useState(initialPromoCodes);
  const [message, setMessage] = useState<Message | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [form, setForm] = useState({
    code: "",
    creditsValue: "200",
    maxUses: "1",
    expiresAt: "",
  });

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsCreating(true);
    setMessage(null);

    try {
      const response = await fetch("/api/admin/promo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: form.code.trim() || undefined,
          creditsValue: Number(form.creditsValue),
          maxUses: Number(form.maxUses),
          expiresAt: form.expiresAt ? new Date(form.expiresAt).toISOString() : null,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Failed to create promo code.");
      }

      setPromoCodes((current) => [data.promoCode, ...current]);
      setForm({ code: "", creditsValue: "200", maxUses: "1", expiresAt: "" });
      setMessage({ type: "success", text: `Promo code ${data.promoCode.code} created.` });
      router.refresh();
    } catch (error) {
      const text = error instanceof Error ? error.message : "Failed to create promo code.";
      setMessage({ type: "error", text });
    } finally {
      setIsCreating(false);
    }
  }

  async function handleToggle(id: string, isActive: boolean) {
    setPendingId(id);
    setMessage(null);

    try {
      const response = await fetch(`/api/admin/promo/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ isActive: !isActive }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Failed to update promo code.");
      }

      setPromoCodes((current) =>
        current.map((promoCode) => (promoCode.id === id ? data.promoCode : promoCode))
      );
      setMessage({
        type: "success",
        text: `Promo code ${data.promoCode.code} ${data.promoCode.isActive ? "activated" : "deactivated"}.`,
      });
      router.refresh();
    } catch (error) {
      const text = error instanceof Error ? error.message : "Failed to update promo code.";
      setMessage({ type: "error", text });
    } finally {
      setPendingId(null);
    }
  }

  async function handleCopy(code: string) {
    try {
      await navigator.clipboard.writeText(code);
      setMessage({ type: "success", text: `Copied ${code} to clipboard.` });
    } catch {
      setMessage({ type: "error", text: "Clipboard access failed." });
    }
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <div className="min-w-0 rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-xl backdrop-blur">
          <div className="mb-6 flex items-start gap-3">
            <div className="rounded-2xl bg-emerald-500/10 p-3 text-emerald-300">
              <Plus className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Generate redeem code</h2>
              <p className="mt-1 text-sm text-slate-400">
                Leave the code blank to auto-generate a secure branded code.
              </p>
            </div>
          </div>

          <form className="space-y-4" onSubmit={handleCreate}>
            <label className="block space-y-2 text-sm">
              <span className="text-slate-300">Code</span>
              <Input
                value={form.code}
                onChange={(event) => setForm((current) => ({ ...current, code: event.target.value.toUpperCase() }))}
                placeholder="CLAIM-VIP-2026"
                className="border-white/10 bg-slate-900/50 text-white placeholder:text-slate-500"
                disabled={isCreating}
              />
            </label>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block space-y-2 text-sm">
                <span className="text-slate-300">Credits</span>
                <Input
                  type="number"
                  min="1"
                  value={form.creditsValue}
                  onChange={(event) => setForm((current) => ({ ...current, creditsValue: event.target.value }))}
                  className="border-white/10 bg-slate-900/50 text-white"
                  disabled={isCreating}
                />
              </label>
              <label className="block space-y-2 text-sm">
                <span className="text-slate-300">Max uses</span>
                <Input
                  type="number"
                  min="1"
                  value={form.maxUses}
                  onChange={(event) => setForm((current) => ({ ...current, maxUses: event.target.value }))}
                  className="border-white/10 bg-slate-900/50 text-white"
                  disabled={isCreating}
                />
              </label>
            </div>

            <label className="block space-y-2 text-sm">
              <span className="text-slate-300">Expiry date</span>
              <div className="relative">
                <Calendar className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <Input
                  type="date"
                  value={form.expiresAt}
                  onChange={(event) => setForm((current) => ({ ...current, expiresAt: event.target.value }))}
                  className="border-white/10 bg-slate-900/50 pl-10 text-white"
                  disabled={isCreating}
                />
              </div>
            </label>

            <Button
              type="submit"
              disabled={isCreating}
              className="h-10 w-full bg-emerald-500 text-white hover:bg-emerald-400"
            >
              {isCreating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              {isCreating ? "Creating..." : "Generate code"}
            </Button>
          </form>
        </div>

        <div className="min-w-0 rounded-3xl border border-white/10 bg-slate-950/60 p-6 shadow-xl backdrop-blur">
          <div className="mb-6 flex items-start justify-between gap-4">
            <div>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
                <TicketPercent className="h-5 w-5 text-sky-400" />
                Promo inventory
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                Track usage, expiry, and deactivate leaked or one-off promo codes.
              </p>
            </div>
            <Badge className="border-white/10 bg-white/5 text-slate-200" variant="outline">
              {promoCodes.length} codes
            </Badge>
          </div>

          {message ? (
            <div
              className={`mb-4 rounded-2xl border px-4 py-3 text-sm ${
                message.type === "success"
                  ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                  : "border-red-500/20 bg-red-500/10 text-red-300"
              }`}
            >
              {message.text}
            </div>
          ) : null}

          {promoCodes.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 px-6 py-12 text-center text-sm text-slate-400">
              No promo codes yet. Generate the first redeem code from the panel on the left.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-white/10 hover:bg-transparent">
                  <TableHead className="text-slate-400">Code</TableHead>
                  <TableHead className="text-slate-400">Credits</TableHead>
                  <TableHead className="text-slate-400">Usage</TableHead>
                  <TableHead className="text-slate-400">Expires</TableHead>
                  <TableHead className="text-slate-400">Status</TableHead>
                  <TableHead className="text-right text-slate-400">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {promoCodes.map((promoCode) => {
                  const usageCount = promoCode._count?.redemptions ?? promoCode.usedCount;
                  return (
                    <TableRow key={promoCode.id} className="border-white/10 hover:bg-white/5">
                      <TableCell className="font-medium text-white">
                        <div className="flex items-center gap-2">
                          <span>{promoCode.code}</span>
                          <button
                            type="button"
                            onClick={() => handleCopy(promoCode.code)}
                            className="rounded-md border border-white/10 p-1 text-slate-400 transition hover:border-sky-400/40 hover:text-sky-300"
                            aria-label={`Copy ${promoCode.code}`}
                          >
                            <Copy className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-300">{promoCode.creditsValue}</TableCell>
                      <TableCell className="text-slate-300">
                        {usageCount} / {promoCode.maxUses}
                      </TableCell>
                      <TableCell className="text-slate-300">
                        {promoCode.expiresAt ? new Date(promoCode.expiresAt).toLocaleDateString() : "No expiry"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          className={promoCode.isActive ? "bg-emerald-500/10 text-emerald-300" : "bg-slate-500/10 text-slate-300"}
                          variant="outline"
                        >
                          {promoCode.isActive ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          type="button"
                          variant={promoCode.isActive ? "destructive" : "secondary"}
                          size="sm"
                          disabled={pendingId === promoCode.id}
                          onClick={() => handleToggle(promoCode.id, promoCode.isActive)}
                        >
                          {pendingId === promoCode.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <Power className="h-4 w-4" />}
                          {promoCode.isActive ? "Deactivate" : "Activate"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </div>
      </section>
    </div>
  );
}
