"use client";

import { useState } from "react";
import { BillItemInput } from "@/types/analyze";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Trash2, Plus } from "lucide-react";

interface Props {
  items: BillItemInput[];
  onChange: (items: BillItemInput[]) => void;
}

export function BillEntryTable({ items, onChange }: Props) {
  const [desc, setDesc] = useState("");
  const [amount, setAmount] = useState("");

  const updateItem = (id: string, updates: Partial<BillItemInput>) => {
    onChange(items.map(item => item.id === id ? { ...item, ...updates } : item));
  };

  const deleteItem = (id: string) => {
    onChange(items.filter(item => item.id !== id));
  };

  const handleAdd = () => {
    if (!desc.trim() || !amount) return;
    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) return;

    onChange([
      ...items,
      {
        id: Math.random().toString(36).substring(7),
        description: desc.trim(),
        billed_amount: parsedAmount,
      }
    ]);
    setDesc("");
    setAmount("");
  };

  const total = items.reduce((sum, item) => sum + item.billed_amount, 0);

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-md border border-white/10 glass">
        <Table className="min-w-[480px]">
          <TableHeader className="bg-white/5 border-b border-white/10">
            <TableRow>
              <TableHead className="text-slate-300 w-2/3">Item Description</TableHead>
              <TableHead className="text-slate-300">Amount (₹)</TableHead>
              <TableHead className="text-slate-300 w-[80px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-slate-500 py-8">
                  No items added yet. Add your bill items below.
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id} className="border-b border-white/5">
                  <TableCell>
                    <Input
                      value={item.description}
                      onChange={(e) => updateItem(item.id, { description: e.target.value })}
                      className="bg-transparent border-0 focus-visible:ring-1 focus-visible:ring-sky-500 text-white"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      value={item.billed_amount}
                      onChange={(e) => updateItem(item.id, { billed_amount: parseFloat(e.target.value) || 0 })}
                      className="bg-transparent border-0 focus-visible:ring-1 focus-visible:ring-sky-500 text-white"
                    />
                  </TableCell>
                  <TableCell>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      onClick={() => deleteItem(item.id)}
                      className="text-slate-400 hover:text-red-400 hover:bg-red-400/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          
          {/* Add Row Form */}
          <TableRow className="bg-sky-500/5">
            <TableCell>
              <Input
                placeholder="e.g. Surgical Gloves"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                className="bg-slate-900/50 border-white/10 text-white placeholder:text-slate-500"
              />
            </TableCell>
            <TableCell>
              <Input
                type="number"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                className="bg-slate-900/50 border-white/10 text-white placeholder:text-slate-500"
              />
            </TableCell>
            <TableCell>
              <Button 
                onClick={handleAdd}
                size="icon"
                className="bg-sky-500 hover:bg-sky-400 text-white w-full"
                disabled={!desc.trim() || !amount}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>

      <div className="flex justify-end pt-2">
        <div className="text-base font-medium text-white sm:text-lg">
          Total Billed: <span className="font-bold ml-2">₹{total.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
