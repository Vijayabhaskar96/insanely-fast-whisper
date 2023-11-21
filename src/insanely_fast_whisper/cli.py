import json

import argparse
import torch
from transformers import pipeline
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn

parser = argparse.ArgumentParser(description="Automatic Speech Recognition")
parser.add_argument(
    "--file-name",
    required=True,
    type=str,
    help="Path or URL to the audio file to be transcribed.",
)
parser.add_argument(
    "--device-id",
    required=False,
    default="0",
    type=str,
    help='Device ID for your CUDA GPU (just pass the device ID number) or pass "mps" for M1/ M2. (default: "0")',
)
parser.add_argument(
    "--transcript-path",
    required=False,
    default="output.json",
    type=str,
    help="Path to save the transcription output. (default: output.json)",
)
parser.add_argument(
    "--model-name",
    required=False,
    default="openai/whisper-large-v3",
    type=str,
    help="Name of the pretrained model/ checkpoint to perform ASR. (default: openai/whisper-large-v3)",
)
parser.add_argument(
    "--task",
    required=False,
    default="transcribe",
    type=str,
    choices=["transcribe", "translate"],
    help="Task to perform: transcribe or translate to another language. (default: transcribe)",
)
parser.add_argument(
    "--language",
    required=False,
    type=str,
    default="None",
    help='Language of the input audio. (default: "None" (Whisper auto-detects the language))',
)
parser.add_argument(
    "--batch-size",
    required=False,
    type=int,
    default=24,
    help="Number of parallel batches you want to compute. Reduce if you face OOMs. (default: 24)",
)
parser.add_argument(
    "--flash",
    required=False,
    type=bool,
    default=False,
    help="Use Flash Attention 2. Read the FAQs to see how to install FA2 correctly. (default: False)",
)
parser.add_argument(
    "--timestamp",
    required=False,
    type=str,
    default="chunk",
    choices=["chunk", "word"],
    help="Whisper supports both chunked as well as word level timestamps. (default: chunk)",
)


def main():
    args = parser.parse_args()

    if args.device_id == "mps":
        pipe = pipeline(
            "automatic-speech-recognition",
            model=args.model_name,
            torch_dtype=torch.float16,
            device="mps",
        )

    elif args.flash == True:
        pipe = pipeline(
            "automatic-speech-recognition",
            model=args.model_name,
            torch_dtype=torch.float16,
            device=f"cuda:{args.device_id}",
            model_kwargs={"use_flash_attention_2": True},
        )

    else:
        pipe = pipeline(
            "automatic-speech-recognition",
            model=args.model_name,
            torch_dtype=torch.float16,
            device=f"cuda:{args.device_id}",
        )

        pipe.model = pipe.model.to_bettertransformer()

    if args.timestamp == "word":
        ts = "word"

    else:
        ts = True

    if args.language == "None":
        lang = None

    else:
        lang = args.language

    with Progress(
        TextColumn("🤗 [progress.description]{task.description}"),
        BarColumn(style="yellow1", pulse_style="white"),
        TimeElapsedColumn(),
    ) as progress:
        progress.add_task("[yellow]Transcribing...", total=None)

        outputs = pipe(
            args.file_name,
            chunk_length_s=30,
            batch_size=args.batch_size,
            generate_kwargs={"task": args.task, "language": lang},
            return_timestamps=ts,
        )

    with open(args.transcript_path, "w", encoding="utf8") as fp:
        json.dump(outputs, fp, ensure_ascii=False)

    print(
        f"Voila! Your file has been transcribed go check it out over here! {args.transcript_path}"
    )
