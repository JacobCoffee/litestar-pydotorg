# Domain Patterns

Recipes for creating and organizing business domains in litestar-pydotorg.

## Create a Complete Domain

This recipe shows how to create a full domain with model, schema, service, and controller.

### Directory Structure

```
src/pydotorg/domains/products/
├── __init__.py
├── models.py
├── schemas.py
├── services.py
├── controllers.py
├── repositories.py
└── dependencies.py
```

### Model

```python
# domains/products/models.py
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pydotorg.core.database import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from pydotorg.domains.users.models import User


class Product(Base, UUIDPrimaryKey, TimestampMixin):
    """Product model."""

    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(back_populates="products")

    def __str__(self) -> str:
        return self.name
```

### Schemas

```python
# domains/products/schemas.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Base product schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: float = Field(..., gt=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a product."""

    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    price: float | None = Field(None, gt=0)
    is_active: bool | None = None


class ProductRead(ProductBase):
    """Schema for reading a product."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class ProductList(BaseModel):
    """Schema for listing products."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    price: float
    is_active: bool
```

### Service

```python
# domains/products/services.py
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Product
from .schemas import ProductCreate, ProductUpdate

if TYPE_CHECKING:
    from collections.abc import Sequence


class ProductService:
    """Service for product operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ProductCreate, owner_id: UUID) -> Product:
        """Create a new product."""
        product = Product(
            **data.model_dump(),
            owner_id=owner_id,
        )
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_by_id(self, product_id: UUID) -> Product | None:
        """Get a product by ID."""
        return await self.session.get(Product, product_id)

    async def list_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = True,
    ) -> Sequence[Product]:
        """List products with pagination."""
        query = select(Product).limit(limit).offset(offset)
        if active_only:
            query = query.where(Product.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(
        self,
        product: Product,
        data: ProductUpdate,
    ) -> Product:
        """Update a product."""
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        """Delete a product."""
        await self.session.delete(product)
        await self.session.flush()
```

### Controller

```python
# domains/products/controllers.py
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from pydotorg.core.guards import require_authenticated
from pydotorg.domains.users.models import User

from .schemas import ProductCreate, ProductList, ProductRead, ProductUpdate
from .services import ProductService

if TYPE_CHECKING:
    from collections.abc import Sequence


class ProductController(Controller):
    """Product API endpoints."""

    path = "/products"
    tags = ["Products"]

    @get("/")
    async def list_products(
        self,
        db_session: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ProductList]:
        """List all active products."""
        service = ProductService(db_session)
        products = await service.list_all(limit=limit, offset=offset)
        return [ProductList.model_validate(p) for p in products]

    @get("/{product_id:uuid}")
    async def get_product(
        self,
        db_session: AsyncSession,
        product_id: UUID,
    ) -> ProductRead:
        """Get a product by ID."""
        service = ProductService(db_session)
        product = await service.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail="Product not found")
        return ProductRead.model_validate(product)

    @post("/", guards=[require_authenticated])
    async def create_product(
        self,
        db_session: AsyncSession,
        data: ProductCreate,
        current_user: User,
    ) -> ProductRead:
        """Create a new product."""
        service = ProductService(db_session)
        product = await service.create(data, owner_id=current_user.id)
        return ProductRead.model_validate(product)

    @patch("/{product_id:uuid}", guards=[require_authenticated])
    async def update_product(
        self,
        db_session: AsyncSession,
        product_id: UUID,
        data: ProductUpdate,
        current_user: User,
    ) -> ProductRead:
        """Update a product."""
        service = ProductService(db_session)
        product = await service.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail="Product not found")
        if product.owner_id != current_user.id:
            raise NotFoundException(detail="Product not found")
        product = await service.update(product, data)
        return ProductRead.model_validate(product)

    @delete("/{product_id:uuid}", guards=[require_authenticated])
    async def delete_product(
        self,
        db_session: AsyncSession,
        product_id: UUID,
        current_user: User,
    ) -> None:
        """Delete a product."""
        service = ProductService(db_session)
        product = await service.get_by_id(product_id)
        if not product:
            raise NotFoundException(detail="Product not found")
        if product.owner_id != current_user.id:
            raise NotFoundException(detail="Product not found")
        await service.delete(product)
```

### Register the Domain

```python
# domains/products/__init__.py
from .controllers import ProductController
from .models import Product
from .schemas import ProductCreate, ProductRead, ProductUpdate
from .services import ProductService

__all__ = [
    "Product",
    "ProductController",
    "ProductCreate",
    "ProductRead",
    "ProductService",
    "ProductUpdate",
]
```

```python
# In main.py or routes.py
from pydotorg.domains.products import ProductController

app = Litestar(
    route_handlers=[
        ProductController,
        # ... other controllers
    ],
)
```

## Domain with Repository Pattern

For complex queries, add a repository layer.

### Repository

```python
# domains/products/repositories.py
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Product

if TYPE_CHECKING:
    from collections.abc import Sequence


class ProductRepository:
    """Repository for product data access."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_owner(
        self,
        owner_id: UUID,
        *,
        active_only: bool = True,
    ) -> Sequence[Product]:
        """Get products by owner."""
        query = select(Product).where(Product.owner_id == owner_id)
        if active_only:
            query = query.where(Product.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def search(
        self,
        query_text: str,
        *,
        limit: int = 20,
    ) -> Sequence[Product]:
        """Search products by name."""
        query = (
            select(Product)
            .where(Product.name.ilike(f"%{query_text}%"))
            .where(Product.is_active == True)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_price_range(self) -> tuple[float, float]:
        """Get min and max prices."""
        query = select(
            func.min(Product.price),
            func.max(Product.price),
        ).where(Product.is_active == True)
        result = await self.session.execute(query)
        row = result.one()
        return (row[0] or 0.0, row[1] or 0.0)
```

### Updated Service

```python
# domains/products/services.py
from .repositories import ProductRepository


class ProductService:
    """Service for product operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProductRepository(session)

    async def get_user_products(self, user_id: UUID) -> Sequence[Product]:
        """Get all products for a user."""
        return await self.repository.get_by_owner(user_id)

    async def search_products(self, query: str) -> Sequence[Product]:
        """Search products."""
        return await self.repository.search(query)
```

## Domain with Events

Add domain events for decoupled communication.

### Event Definitions

```python
# domains/products/events.py
from dataclasses import dataclass
from uuid import UUID


@dataclass
class ProductCreatedEvent:
    """Event fired when a product is created."""

    product_id: UUID
    owner_id: UUID
    name: str


@dataclass
class ProductDeletedEvent:
    """Event fired when a product is deleted."""

    product_id: UUID
    owner_id: UUID
```

### Event Handlers

```python
# domains/products/handlers.py
import logging

from .events import ProductCreatedEvent, ProductDeletedEvent

logger = logging.getLogger(__name__)


async def on_product_created(event: ProductCreatedEvent) -> None:
    """Handle product created event."""
    logger.info(f"Product created: {event.name} ({event.product_id})")
    # Update search index, send notifications, etc.


async def on_product_deleted(event: ProductDeletedEvent) -> None:
    """Handle product deleted event."""
    logger.info(f"Product deleted: {event.product_id}")
    # Remove from search index, cleanup, etc.
```

### Service with Events

```python
# domains/products/services.py
from .events import ProductCreatedEvent, ProductDeletedEvent


class ProductService:
    def __init__(
        self,
        session: AsyncSession,
        event_bus: EventBus | None = None,
    ) -> None:
        self.session = session
        self.event_bus = event_bus

    async def create(self, data: ProductCreate, owner_id: UUID) -> Product:
        product = Product(**data.model_dump(), owner_id=owner_id)
        self.session.add(product)
        await self.session.flush()

        if self.event_bus:
            await self.event_bus.publish(
                ProductCreatedEvent(
                    product_id=product.id,
                    owner_id=owner_id,
                    name=product.name,
                )
            )

        return product
```

## Domain with Background Tasks

Integrate with SAQ for background processing.

### Task Definitions

```python
# domains/products/tasks.py
from uuid import UUID

from saq import Job

from pydotorg.tasks.base import queue


async def process_product_images(ctx: dict, product_id: UUID) -> None:
    """Process and optimize product images."""
    # Get product from database
    # Download images
    # Process and optimize
    # Upload to CDN
    pass


async def update_product_index(ctx: dict, product_id: UUID) -> None:
    """Update product in search index."""
    # Get product data
    # Update Meilisearch index
    pass
```

### Enqueue Tasks from Service

```python
# domains/products/services.py
from .tasks import process_product_images, update_product_index


class ProductService:
    async def create(self, data: ProductCreate, owner_id: UUID) -> Product:
        product = Product(**data.model_dump(), owner_id=owner_id)
        self.session.add(product)
        await self.session.flush()

        # Enqueue background tasks
        await queue.enqueue(
            "process_product_images",
            product_id=product.id,
        )
        await queue.enqueue(
            "update_product_index",
            product_id=product.id,
        )

        return product
```

## See Also

- [Testing Recipes](testing-recipes.md) - Testing domains
- [Database Recipes](database-recipes.md) - Query and transaction patterns
- [Authentication Recipes](authentication-recipes.md) - Auth flows
