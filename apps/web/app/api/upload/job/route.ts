import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { auth } from "@/lib/auth";
import { FileType } from "@prisma/client";

export async function POST(req: Request) {
  try {
    const { jobId, key, originalFilename, fileType } = await req.json();

    if (!jobId || !key || !originalFilename || !fileType) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    const session = await auth();
    if (!session?.user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    const userId = session.user.id;

    const job = await prisma.uploadJob.create({
      data: {
        id: jobId,
        userId: userId as string,
        r2Key: key,
        originalFilename,
        fileType: fileType as FileType,
        status: "PENDING",
      },
    });

    return NextResponse.json(job);
  } catch (error) {
    console.error("UploadJob creation error:", error);
    return NextResponse.json({ error: "Failed to create job" }, { status: 500 });
  }
}
