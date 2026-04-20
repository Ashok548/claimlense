import { NextResponse } from "next/server";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import crypto from "crypto";
import { auth } from "@/lib/auth";

const s3Client = new S3Client({
  region: "auto",
  endpoint: process.env.R2_ENDPOINT_URL!,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
  },
  forcePathStyle: true,
  requestChecksumCalculation: "WHEN_REQUIRED",
  responseChecksumValidation: "WHEN_REQUIRED",
});

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const { filename, contentType } = await req.json();

    if (!filename || !contentType) {
      return NextResponse.json({ error: "Missing filename or contentType" }, { status: 400 });
    }

    // Validate File Format
    const allowedTypes = ["application/pdf", "image/jpeg", "image/png", "application/octet-stream"];
    if (!allowedTypes.includes(contentType)) {
      return NextResponse.json({ error: "Invalid file type. Only PDF or Images allowed." }, { status: 400 });
    }

    const jobId = crypto.randomUUID();
    const ext = filename.split(".").pop();
    const key = `bills/guest/${jobId}.${ext}`;

    const command = new PutObjectCommand({
      Bucket: process.env.R2_BUCKET_NAME!,
      Key: key,
    });

    const url = await getSignedUrl(s3Client, command, { expiresIn: 3600 });

    return NextResponse.json({ url, key, jobId });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("[R2 ERROR] Presigned URL Error:", message);
    return NextResponse.json({ error: "Failed to generate upload URL" }, { status: 500 });
  }
}
