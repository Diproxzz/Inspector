import os
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, SmallInteger, Numeric, Boolean, LargeBinary, DateTime, ForeignKey, Index, text

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/inspector_qc")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class InspectionBatch(Base):
    __tablename__ = "inspection_batches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="UPLOADING", nullable=False)
    total_images: Mapped[int] = mapped_column(Integer, nullable=False)
    processed_images: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    images: Mapped[list["InspectionImage"]] = relationship("InspectionImage", back_populates="batch", cascade="all, delete-orphan", order_by="InspectionImage.display_order")

class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inspection_batches.id", ondelete="CASCADE"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    capture_timestamp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    perceptual_hash: Mapped[str] = mapped_column(String(32), nullable=False)
    orig_width: Mapped[int] = mapped_column(Integer, nullable=False)
    orig_height: Mapped[int] = mapped_column(Integer, nullable=False)
    orig_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    comp_width: Mapped[int] = mapped_column(Integer, nullable=False)
    comp_height: Mapped[int] = mapped_column(Integer, nullable=False)
    comp_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    compressed_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    excel_blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    section_id: Mapped[int] = mapped_column(SmallInteger, default=11, nullable=False)
    sub_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    caption_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_product_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    classifier_used: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rotation_deg: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_excluded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    batch: Mapped["InspectionBatch"] = relationship("InspectionBatch", back_populates="images")

    __table_args__ = (
        Index("idx_images_batch_section_order", "batch_id", "section_id", "display_order"),
        Index("idx_images_sha256", "sha256_hash"),
    )

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
