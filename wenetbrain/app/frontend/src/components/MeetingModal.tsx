import { useRef, useState } from "react";
import { Mic, Upload, StopCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface MeetingModalProps {
  open: boolean;
  onClose: () => void;
}

export function MeetingModal({ open, onClose }: MeetingModalProps) {
  const [title, setTitle] = useState("");
  const [type, setType] = useState("company");
  const [participants, setParticipants] = useState("");
  const [source, setSource] = useState<"record" | "upload">("record");
  const [recording, setRecording] = useState(false);
  const [recordedSecs, setRecordedSecs] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function toggleRecording() {
    if (recording && mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      return;
    }

    try {
      let displayStream: MediaStream | null = null;
      let micStream: MediaStream | null = null;
      try {
        displayStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
      } catch {
        // ignore
      }
      try {
        micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (e) {
        if (!displayStream || !displayStream.getAudioTracks().length) {
          alert("Brak dostępu do mikrofonu: " + String(e));
          return;
        }
      }
      const tracks = [
        ...(displayStream?.getTracks() || []),
        ...(micStream?.getTracks() || []),
      ];
      const combined = new MediaStream(tracks);

      const recorder = new MediaRecorder(combined);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioUrl(URL.createObjectURL(blob));
        setRecording(false);
        if (timerRef.current) clearInterval(timerRef.current);
        tracks.forEach((t) => t.stop());
      };

      recorder.start();
      setRecording(true);
      setRecordedSecs(0);
      timerRef.current = setInterval(() => setRecordedSecs((s) => s + 1), 1000);
    } catch (err) {
      alert(String(err));
    }
  }

  function onFileSelected(input: HTMLInputElement) {
    if (input.files && input.files.length) {
      setFile(input.files[0]);
    }
  }

  async function submit() {
    if (!title.trim()) {
      setResult("Uzupełnij tytuł!");
      return;
    }
    setResult("Przesyłanie...");
    setLoading(true);

    const token = localStorage.getItem("wenetbrain_token");
    const headers: HeadersInit = {};
    if (token) headers["Authorization"] = "Bearer " + token;

    try {
      if (source === "upload") {
        if (!file) {
          setResult("Wybierz plik!");
          setLoading(false);
          return;
        }
        const form = new FormData();
        form.append("title", title);
        form.append("meeting_type", type);
        form.append("participants", participants);
        form.append("file", file);
        const res = await fetch("http://localhost:8000/api/meetings/upload", {
          method: "POST",
          headers,
          body: form,
        });
        if (!res.ok) throw new Error("Upload failed");
        const data = await res.json();
        setResult(`Gotowe! ID: ${data.meeting_id}`);
      } else {
        if (!audioUrl) {
          setResult("Nagraj najpierw audio!");
          setLoading(false);
          return;
        }
        const blob = await fetch(audioUrl).then((r) => r.blob());
        const form = new FormData();
        form.append("title", title);
        form.append("meeting_type", type);
        form.append("participants", participants);
        form.append("file", blob, "recording.webm");
        const res = await fetch("http://localhost:8000/api/meetings/upload", {
          method: "POST",
          headers,
          body: form,
        });
        if (!res.ok) throw new Error("Upload failed");
        const data = await res.json();
        setResult(`Gotowe! ID: ${data.meeting_id}`);
      }
    } catch (e) {
      setResult(String(e));
    } finally {
      setLoading(false);
    }
  }

  const formatTime = (s: number) => {
    const m = String(Math.floor(s / 60)).padStart(2, "0");
    const sec = String(s % 60).padStart(2, "0");
    return `${m}:${sec}`;
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg" style={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)" }}>
        <DialogHeader>
          <DialogTitle className="text-base font-bold">Nowe spotkanie</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Tytuł</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="np. Sprint Planning" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Typ</Label>
              <Select value={type} onValueChange={setType}>
                <SelectTrigger className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="company">Firma</SelectItem>
                  <SelectItem value="team">Zespół</SelectItem>
                  <SelectItem value="private">Prywatne</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Uczestnicy</Label>
              <Input value={participants} onChange={(e) => setParticipants(e.target.value)} placeholder="Anna, Marek" className="text-sm" style={{ borderColor: "var(--color-border-secondary)" }} />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-xs font-semibold" style={{ color: "var(--color-text-secondary)" }}>Źródło</Label>
            <div className="flex gap-2">
              <Button
                size="sm"
                type="button"
                onClick={() => setSource("record")}
                className="gap-1"
                style={source === "record" ? { background: "var(--color-accent)", color: "var(--color-primary-foreground)" } : {}}
                variant={source === "record" ? "default" : "outline"}
              >
                <Mic className="w-4 h-4" />
                Nagraj teraz
              </Button>
              <Button
                size="sm"
                type="button"
                onClick={() => setSource("upload")}
                className="gap-1"
                variant={source === "upload" ? "default" : "outline"}
                style={source === "upload" ? { background: "var(--color-accent)", color: "var(--color-primary-foreground)" } : {}}
              >
                <Upload className="w-4 h-4" />
                Załącz plik
              </Button>
            </div>
          </div>

          {source === "record" && (
            <div className="space-y-2">
              <div
                className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors"
                style={{ borderColor: recording ? "var(--color-danger)" : "var(--color-border-secondary)", color: "var(--color-text-tertiary)" }}
                onClick={toggleRecording}
              >
                {recording ? <StopCircle className="w-8 h-8 mx-auto mb-2" style={{ color: "var(--color-danger)" }} /> : <Mic className="w-8 h-8 mx-auto mb-2" />}
                <div className="text-sm font-medium">{recording ? "Zatrzymaj nagrywanie" : "Kliknij aby nagrać"}</div>
                <div className="text-xs mt-1">Mikrofon + dźwięk z komputera</div>
              </div>
              {recording && (
                <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: "color-mix(in oklch, var(--color-danger) 8%, transparent)", border: "1px solid color-mix(in oklch, var(--color-danger) 20%, transparent)" }}>
                  <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: "var(--color-danger)" }} />
                  <span className="text-xl font-bold font-mono" style={{ color: "var(--color-danger)" }}>{formatTime(recordedSecs)}</span>
                  <span className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>Nagrywanie...</span>
                </div>
              )}
              {audioUrl && (
                <audio src={audioUrl} controls className="w-full" />
              )}
            </div>
          )}

          {source === "upload" && (
            <div className="space-y-2">
              <div
                className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors hover:border-[var(--color-accent)]"
                style={{ borderColor: "var(--color-border-secondary)", color: "var(--color-text-tertiary)" }}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-8 h-8 mx-auto mb-2" />
                <div className="text-sm font-medium">Kliknij lub przeciągnij plik</div>
                <div className="text-xs mt-1">WAV, MP3, M4A, TXT</div>
              </div>
              <input ref={fileInputRef} type="file" accept=".wav,.mp3,.m4a,.txt" className="hidden" onChange={(e) => onFileSelected(e.target)} />
              {file && (
                <div className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
                  Wybrano: {file.name} ({Math.round(file.size / 1024)} KB)
                </div>
              )}
            </div>
          )}

          {result && (
            <pre className="text-xs p-2 rounded-md whitespace-pre-wrap" style={{ background: "var(--color-background-secondary)", color: "var(--color-text-secondary)" }}>
              {result}
            </pre>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose} disabled={loading}>Anuluj</Button>
          <Button size="sm" onClick={submit} disabled={loading} style={{ background: "var(--color-primary)", color: "var(--color-primary-foreground)" }}>
            Przetwórz przez AI
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
