-- CreateTable: users
-- Matches the Prisma User model exactly: same column names, types, constraints.
-- "passwordHash", "otpCode", "faceDescriptors" etc. use quoted camelCase to
-- match what Prisma generates and what the backend auth.py queries by name.
CREATE TABLE "users" (
    "id"              TEXT NOT NULL,
    "name"            TEXT NOT NULL,
    "email"           TEXT NOT NULL,
    "passwordHash"    TEXT NOT NULL,
    "mobile"          TEXT,
    "role"            TEXT NOT NULL DEFAULT 'user',
    "otpCode"         TEXT,
    "otpExpiry"       TIMESTAMP(3),
    "otpMobile"       TEXT,
    "faceDescriptors" TEXT,
    "createdAt"       TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt"       TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable: sessions
CREATE TABLE "sessions" (
    "id"        TEXT NOT NULL,
    "token"     TEXT NOT NULL,
    "userId"    TEXT NOT NULL,
    "expiresAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "sessions_pkey" PRIMARY KEY ("id")
);

-- CreateIndex: unique constraints
CREATE UNIQUE INDEX "users_email_key"  ON "users"("email");
CREATE UNIQUE INDEX "users_mobile_key" ON "users"("mobile");
CREATE UNIQUE INDEX "sessions_token_key" ON "sessions"("token");

-- AddForeignKey: sessions.userId → users.id with CASCADE delete
ALTER TABLE "sessions"
    ADD CONSTRAINT "sessions_userId_fkey"
    FOREIGN KEY ("userId")
    REFERENCES "users"("id")
    ON DELETE CASCADE
    ON UPDATE CASCADE;
