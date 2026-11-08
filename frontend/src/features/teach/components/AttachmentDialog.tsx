"use client";

import { ArrowLeftIcon } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";

import {
  ATTACHMENT_KINDS,
  KIND_INFO,
  youtubeId,
} from "@/features/content/attachment-kinds";
import {
  type Attachment,
  type AttachmentKind,
  type Form,
  FORM_LABELS,
  FORMS,
  newBlockId,
} from "@/features/content/types";
import { Button } from "@/shared/ui/button";
import { Checkbox } from "@/shared/ui/checkbox";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { FieldGroup } from "@/shared/ui/field";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";
import { Textarea } from "@/shared/ui/textarea";

import { type ChosenFile, FileUpload } from "./FileUpload";

/** Dialog state: `attachment` is null for a new one. */
export type AttachmentTarget = { attachment: Attachment | null };

type AttachmentDialogProps = {
  target: AttachmentTarget | null;
  onClose: () => void;
  onSave: (attachment: Attachment) => void;
};

export function AttachmentDialog({
  target,
  onClose,
  onSave,
}: AttachmentDialogProps) {
  return (
    <Dialog
      open={target !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent className="max-h-[calc(100svh-2rem)] overflow-y-auto sm:max-w-lg">
        {target && (
          <AttachmentForm
            key={target.attachment?.id ?? "new"}
            attachment={target.attachment}
            onSave={onSave}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

// --- Step 1: kind of a new attachment -------------------------------------------------

function KindPicker({ onPick }: { onPick: (kind: AttachmentKind) => void }) {
  return (
    <>
      <DialogHeader>
        <DialogTitle>Nowy załącznik</DialogTitle>
        <DialogDescription>
          Wybierz, co chcesz dodać do lekcji.
        </DialogDescription>
      </DialogHeader>
      <ul role="list" className="grid gap-2 sm:grid-cols-2">
        {ATTACHMENT_KINDS.map((kind) => {
          const { label, description, icon: Icon } = KIND_INFO[kind];
          return (
            <li key={kind}>
              <button
                type="button"
                onClick={() => onPick(kind)}
                className="flex h-full w-full items-start gap-3 rounded-xl p-3 text-left ring-1 ring-foreground/10 transition-colors outline-none hover:bg-muted/50 focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
                <span>
                  <span className="block font-medium">{label}</span>
                  <span className="block text-muted-foreground">
                    {description}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </>
  );
}

// --- Step 2: fields of the kind -------------------------------------------------------

type FormValues = {
  title: string;
  description: string;
  forms: Form[];
  alt: string;
  youtube_url: string;
  transcript: string;
  url: string;
};

/** Second source of a video (YouTube) or a recording (text for the reader). */
type Source = "file" | "other";

const titleRules = {
  validate: (value: string) => value.trim() !== "" || "Wpisz tytuł załącznika.",
  maxLength: { value: 120, message: "Tytuł może mieć najwyżej 120 znaków." },
};
const shortTextRules = {
  maxLength: { value: 500, message: "Tekst może mieć najwyżej 500 znaków." },
};

function savedFile(attachment: Attachment | null): ChosenFile | null {
  if (!attachment || !("file_id" in attachment) || !attachment.file_id) {
    return null;
  }
  return {
    id: attachment.file_id,
    name: attachment.file_name ?? "Plik",
    url: attachment.file_url ?? `/files/${attachment.file_id}`,
  };
}

function initialSource(attachment: Attachment | null): Source {
  if (attachment?.kind === "video" && attachment.youtube_url) {
    return "other";
  }
  if (attachment?.kind === "audio" && attachment.transcript) {
    return "other";
  }
  return "file";
}

type AttachmentFormProps = {
  attachment: Attachment | null;
  onSave: (attachment: Attachment) => void;
};

function AttachmentForm({ attachment, onSave }: AttachmentFormProps) {
  const [kind, setKind] = useState<AttachmentKind | null>(
    attachment?.kind ?? null,
  );
  const [file, setFile] = useState<ChosenFile | null>(savedFile(attachment));
  const [fileError, setFileError] = useState<string>();
  const [source, setSource] = useState<Source>(initialSource(attachment));
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    defaultValues: {
      title: attachment?.title ?? "",
      description: attachment?.description ?? "",
      forms: attachment?.forms ?? [],
      alt: attachment?.kind === "image" ? (attachment.alt ?? "") : "",
      youtube_url:
        attachment?.kind === "video" ? (attachment.youtube_url ?? "") : "",
      transcript:
        attachment?.kind === "audio" ? (attachment.transcript ?? "") : "",
      url: attachment?.kind === "link" ? attachment.url : "",
    },
  });

  if (kind === null) {
    return <KindPicker onPick={setKind} />;
  }

  const usesFile =
    kind === "image" ||
    kind === "pdf" ||
    ((kind === "video" || kind === "audio") && source === "file");

  const onSubmit = handleSubmit((values) => {
    if (usesFile && !file) {
      return; // the message is set in the submit handler below
    }
    const base = {
      id: attachment?.id ?? newBlockId(),
      type: "attachment" as const,
      title: values.title.trim(),
      forms: FORMS.filter((form) => values.forms.includes(form)),
      ...(values.description.trim() && {
        description: values.description.trim(),
      }),
    };
    // Display fields let the editor show the file before the lesson is saved
    const fileFields = file
      ? { file_id: file.id, file_name: file.name, file_url: file.url }
      : null;
    switch (kind) {
      case "image":
        onSave({ ...base, kind, ...fileFields!, alt: values.alt.trim() });
        break;
      case "pdf":
        onSave({ ...base, kind, ...fileFields! });
        break;
      case "video":
        onSave(
          source === "file"
            ? { ...base, kind, ...fileFields! }
            : { ...base, kind, youtube_url: values.youtube_url.trim() },
        );
        break;
      case "audio":
        onSave(
          source === "file"
            ? { ...base, kind, ...fileFields! }
            : { ...base, kind, transcript: values.transcript.trim() },
        );
        break;
      case "link":
        onSave({ ...base, kind, url: values.url.trim() });
        break;
    }
  });

  const fileField = (fileKind: "image" | "audio" | "video" | "pdf") => (
    <FormField label="Plik">
      {(field) => (
        <FileUpload
          {...field}
          kind={fileKind}
          value={file}
          error={fileError}
          onChange={(chosen) => {
            setFile(chosen);
            setFileError(undefined);
          }}
        />
      )}
    </FormField>
  );

  const info = KIND_INFO[kind];

  return (
    <form
      noValidate
      className="grid gap-4"
      onSubmit={(event) => {
        // Portaled dialog: keep the submit away from any form around it
        event.stopPropagation();
        // Checked here, so it shows together with the other field errors
        if (usesFile && !file) {
          setFileError("Dodaj plik.");
        }
        void onSubmit(event);
      }}
    >
      <DialogHeader>
        <DialogTitle>
          {attachment
            ? `Edycja: ${info.label}`
            : `Nowy załącznik: ${info.label}`}
        </DialogTitle>
        {!attachment && (
          <Button
            type="button"
            variant="link"
            className="h-auto w-fit p-0"
            onClick={() => setKind(null)}
          >
            <ArrowLeftIcon data-icon="inline-start" />
            Wybierz inny typ
          </Button>
        )}
      </DialogHeader>

      <FieldGroup>
        {kind === "image" && (
          <>
            {fileField("image")}
            <FormField
              label="Opis obrazu"
              description="Dla osób, które nie widzą obrazu (czytnik ekranu)."
              error={errors.alt?.message}
            >
              {(field) => (
                <Input {...field} {...register("alt", shortTextRules)} />
              )}
            </FormField>
          </>
        )}

        {kind === "pdf" && fileField("pdf")}

        {(kind === "video" || kind === "audio") && (
          <Tabs
            value={source}
            onValueChange={(value) => {
              setSource(value as Source);
              setFileError(undefined);
            }}
          >
            <TabsList>
              <TabsTrigger value="file">Plik</TabsTrigger>
              <TabsTrigger value="other">
                {kind === "video" ? "YouTube" : "Tekst dla lektora"}
              </TabsTrigger>
            </TabsList>
            <TabsContent value="file" className="pt-2">
              {fileField(kind)}
            </TabsContent>
            <TabsContent value="other" className="pt-2">
              {kind === "video" ? (
                <FormField
                  label="Adres filmu na YouTube"
                  error={errors.youtube_url?.message}
                >
                  {(field) => (
                    <Input
                      {...field}
                      type="url"
                      placeholder="https://youtu.be/…"
                      {...register("youtube_url", {
                        validate: (value) =>
                          source !== "other" ||
                          youtubeId(value) !== null ||
                          "Wklej adres filmu z YouTube, np. https://youtu.be/abc123XYZ_0.",
                      })}
                    />
                  )}
                </FormField>
              ) : (
                <FormField
                  label="Tekst dla lektora"
                  description="Przeglądarka przeczyta go na głos; uczeń zobaczy go też jako tekst."
                  error={errors.transcript?.message}
                >
                  {(field) => (
                    <Textarea
                      {...field}
                      rows={5}
                      {...register("transcript", {
                        validate: (value) =>
                          source !== "other" ||
                          value.trim() !== "" ||
                          "Wpisz tekst, który przeczyta lektor.",
                        maxLength: {
                          value: 5000,
                          message: "Tekst może mieć najwyżej 5000 znaków.",
                        },
                      })}
                    />
                  )}
                </FormField>
              )}
            </TabsContent>
          </Tabs>
        )}

        {kind === "link" && (
          <FormField label="Adres strony" error={errors.url?.message}>
            {(field) => (
              <Input
                {...field}
                type="url"
                placeholder="https://"
                {...register("url", {
                  validate: (value) =>
                    /^https:\/\/[^\s/]+\.[^\s]+$/i.test(value.trim()) ||
                    "Wpisz pełny adres zaczynający się od https://, np. https://pl.wikipedia.org.",
                })}
              />
            )}
          </FormField>
        )}

        <FormField label="Tytuł" error={errors.title?.message}>
          {(field) => (
            <Input
              {...field}
              autoComplete="off"
              {...register("title", titleRules)}
            />
          )}
        </FormField>
        <FormField
          label="Opis (opcjonalnie)"
          error={errors.description?.message}
        >
          {(field) => (
            <Textarea
              {...field}
              rows={2}
              {...register("description", shortTextRules)}
            />
          )}
        </FormField>

        <Controller
          control={control}
          name="forms"
          rules={{
            validate: (value) =>
              value.length > 0 || "Zaznacz co najmniej jedną formę.",
          }}
          render={({ field, fieldState }) => (
            <fieldset
              className="space-y-3"
              aria-describedby={fieldState.error ? "forms-error" : undefined}
            >
              <legend className="mb-3 text-sm font-medium">Formy</legend>
              {FORMS.map((form) => (
                <label
                  key={form}
                  className="flex min-h-control cursor-pointer items-center gap-3 text-base"
                >
                  <Checkbox
                    checked={field.value.includes(form)}
                    onCheckedChange={(checked) =>
                      field.onChange(
                        checked
                          ? [...field.value, form]
                          : field.value.filter((item) => item !== form),
                      )
                    }
                    aria-invalid={fieldState.error ? true : undefined}
                  />
                  {FORM_LABELS[form]}
                </label>
              ))}
              {fieldState.error && (
                <p
                  id="forms-error"
                  role="alert"
                  className="text-sm text-destructive"
                >
                  {fieldState.error.message}
                </p>
              )}
            </fieldset>
          )}
        />
      </FieldGroup>

      <DialogFooter>
        <DialogClose render={<Button type="button" variant="outline" />}>
          Anuluj
        </DialogClose>
        <Button type="submit">{attachment ? "Zapisz" : "Dodaj"}</Button>
      </DialogFooter>
    </form>
  );
}
