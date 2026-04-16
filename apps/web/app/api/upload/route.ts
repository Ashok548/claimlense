import { NextResponse } from "next/server";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { FileType } from "@prisma/client";
import crypto from "crypto";

// Server-side S3 client — no CORS issues since this runs on the server
const s3Client = new S3Client({
  region: "auto",
  endpoint: process.env.R2_ENDPOINT_URL!,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!,
  },
  requestChecksumCalculation: "WHEN_REQUIRED",
  responseChecksumValidation: "WHEN_REQUIRED",
});

export async function POST(req: Request) {
  try {
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const userId = session.user.id;

    // Parse multipart form data
    const formData = await req.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    // Validate file type
    const allowedTypes = ["application/pdf", "image/jpeg", "image/png"];
    if (!allowedTypes.includes(file.type)) {
      return NextResponse.json(
        { error: "Invalid file type. Only PDF, JPG, and PNG are allowed." },
        { status: 400 }
      );
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      return NextResponse.json({ error: "File too large. Max 10MB." }, { status: 400 });
    }

    // Generate unique key
    const jobId = crypto.randomUUID();
    const ext = file.name.split(".").pop();
    const key = `bills/${userId}/${jobId}.${ext}`;

    // Read file buffer
    const buffer = Buffer.from(await file.arrayBuffer());

    // Upload directly to R2 (server-to-server — no CORS restrictions)
    await s3Client.send(
      new PutObjectCommand({
        Bucket: process.env.R2_BUCKET_NAME!,
        Key: key,
        Body: buffer,
        ContentType: file.type,
        ContentLength: buffer.byteLength,
      })
    );

    console.log(`[UPLOAD] File uploaded to R2: ${key}`);

    // Register the upload job in DB
    const fileType: FileType = file.type === "application/pdf" ? "PDF" : "IMAGE";
    const job = await prisma.uploadJob.create({
      data: {
        id: jobId,
        userId: userId as string,
        r2Key: key,
        originalFilename: file.name,
        fileType,
        status: "PENDING",
      },
    });

    return NextResponse.json({ key, jobId: job.id });
  } catch (error: any) {
    console.error("[UPLOAD ERROR]", error?.message || error);
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}
