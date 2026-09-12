"use client";

import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/cricshift/navbar";
import { useUploadHistoricalDataset } from "@/lib/api/historical";
import { FileUp, File, Loader2, ArrowRight, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export default function HistoricalUploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const uploadMutation = useUploadHistoricalDataset();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith(".csv") || droppedFile.type === "text/csv" || droppedFile.type === "application/vnd.ms-excel") {
        setFile(droppedFile);
      } else {
        alert("Please upload a valid .csv file.");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleAnalyze = () => {
    if (!file) return;
    
    uploadMutation.mutate(file, {
      onSuccess: (data) => {
        // Store result in sessionStorage to pass to the analysis page.
        // sessionStorage has a ~5 MB limit; catch QuotaExceededError gracefully.
        const key = `analysis_${data.analysis_id}`;
        try {
          sessionStorage.setItem(key, JSON.stringify(data));
        } catch (storageErr) {
          // If the payload is too large for sessionStorage (e.g. long Test match),
          // we still navigate — the analysis page should handle missing storage
          // gracefully and show a friendly message.
          console.warn(
            "[historical] sessionStorage quota exceeded — analysis data not cached.",
            storageErr
          );
        }
        router.push(`/historical/${data.analysis_id}`);
      },
    });
  };

  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />
      
      <main className="flex flex-1 flex-col items-center justify-center px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto w-full pt-20">
        
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-4 py-1.5 text-sm font-medium text-amber-400 mb-6">
            <FileUp className="h-4 w-4" />
            Historical Match Analysis
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl mb-4">
            Upload Match Data
          </h1>
          <p className="max-w-xl text-lg text-muted-foreground mx-auto">
            Upload a ball-by-ball CSV dataset to generate a complete intelligence timeline, detecting momentum shifts and visualizing win probabilities.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="w-full max-w-2xl"
        >
          <div
            className={cn(
              "relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 transition-all",
              isDragging
                ? "border-emerald-500 bg-emerald-500/10"
                : file
                ? "border-amber-500/50 bg-white/[0.02]"
                : "border-white/20 bg-white/[0.02] hover:border-white/40 hover:bg-white/[0.04]"
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !file && fileInputRef.current?.click()}
            style={{ cursor: file ? "default" : "pointer" }}
          >
            <input
              type="file"
              accept=".csv"
              className="hidden"
              ref={fileInputRef}
              onChange={handleFileChange}
            />

            {file ? (
              <div className="flex flex-col items-center gap-4 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/20 text-amber-400">
                  <File className="h-8 w-8" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">{file.name}</h3>
                  <p className="text-sm text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                
                <div className="mt-6 flex gap-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                      uploadMutation.reset();
                    }}
                    className="rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-white/10"
                    disabled={uploadMutation.isPending}
                  >
                    Remove
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAnalyze();
                    }}
                    disabled={uploadMutation.isPending}
                    className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 px-6 py-2 text-sm font-semibold text-amber-950 transition-transform hover:scale-[1.03] disabled:opacity-70 disabled:hover:scale-100"
                  >
                    {uploadMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        Analyze Timeline
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4 text-center pointer-events-none">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/5 text-muted-foreground">
                  <FileUp className="h-8 w-8" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Click or drag CSV here</h3>
                  <p className="text-sm text-muted-foreground mt-1">Must contain ball-by-ball match data.</p>
                </div>
              </div>
            )}
          </div>
          
          {uploadMutation.isError && (
            <div className="mt-6 rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <p>Failed to analyze the dataset. Please ensure the CSV contains required features (Match_ID, Innings, Over, Ball, Batter, Bowler, Current_Score, Wicket).</p>
            </div>
          )}

        </motion.div>
      </main>
    </div>
  );
}
