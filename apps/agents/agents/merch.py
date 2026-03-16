"""
Merch Agent
Plans and executes merch drops tied to releases — from design briefs
to Shopify listings, fulfillment, inventory, and margin calculations.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from base_agent import BaseAgent, AgentTask, AgentResult

logger = logging.getLogger(__name__)

# Product type pricing ranges (min, max)
PRICING = {
    "t-shirt":  (25.0, 35.0),
    "hoodie":   (50.0, 70.0),
    "hat":      (25.0, 35.0),
    "sticker":  (5.0, 10.0),
    "vinyl":    (25.0, 40.0),
    "poster":   (15.0, 25.0),
    "bundle":   (60.0, 100.0),
}

# Margin targets by model
MARGIN_TARGETS = {
    "pod":      (0.40, 0.50),   # Print-on-demand
    "bulk":     (0.60, 0.70),   # Bulk manufactured
    "limited":  (0.70, 0.80),   # Limited edition
    "digital":  (0.90, 0.99),   # Digital goods
}

# Cost multipliers (cost as fraction of retail price)
COST_ESTIMATES = {
    "t-shirt": 0.35,
    "hoodie": 0.40,
    "hat": 0.38,
    "sticker": 0.15,
    "vinyl": 0.45,
    "poster": 0.25,
    "bundle": 0.38,
}

# Standard reorder point (units)
REORDER_POINT = 20


class MerchAgent(BaseAgent):
    agent_id = "merch"
    agent_name = "Merch Agent"
    subscriptions = ["release.distributed", "artist.milestone"]

    async def handle_task(self, task: AgentTask) -> AgentResult:
        handlers = {
            "plan_merch_drop": self._plan_merch_drop,
            "create_product_listing": self._create_product_listing,
            "process_order": self._process_order,
            "track_inventory": self._track_inventory,
            "generate_design_brief": self._generate_design_brief,
            "calculate_margins": self._calculate_margins,
            # Legacy
            "design_brief": self._generate_design_brief,
            "launch_store": self._launch_store,
            "inventory_check": self._track_inventory,
            "merch_report": self._merch_report,
        }
        handler = handlers.get(task.task_type)
        result = await handler(task) if handler else {"status": "unknown_task", "task_type": task.task_type}
        return AgentResult(success=True, task_id=task.task_id, agent_id=self.agent_id, result=result)

    # ----------------------------------------------------------------
    # plan_merch_drop
    # ----------------------------------------------------------------

    async def _plan_merch_drop(self, task: AgentTask) -> dict:
        p = task.payload
        artist_id = p.get("artist_id") or task.artist_id
        release_id = p.get("release_id") or task.release_id
        release_date_str = p.get("release_date")
        priority = p.get("priority", "standard")

        # Determine product lineup based on priority
        if priority == "priority":
            products = ["t-shirt", "hoodie", "hat", "sticker", "vinyl", "poster", "bundle"]
        else:
            products = ["t-shirt", "hoodie", "sticker", "poster"]

        # Build timeline relative to release date
        if release_date_str:
            try:
                release_date = datetime.fromisoformat(release_date_str.replace("Z", "+00:00"))
            except Exception:
                release_date = datetime.now(timezone.utc) + timedelta(weeks=4)
        else:
            release_date = datetime.now(timezone.utc) + timedelta(weeks=4)

        timeline = {
            "t_minus_4_weeks": {
                "date": (release_date - timedelta(weeks=4)).strftime("%Y-%m-%d"),
                "milestone": "Design brief sent to Creative Agent",
                "owner": "merch → creative",
            },
            "t_minus_3_weeks": {
                "date": (release_date - timedelta(weeks=3)).strftime("%Y-%m-%d"),
                "milestone": "Mockups delivered by Creative Agent",
                "owner": "creative → merch",
            },
            "t_minus_2_weeks": {
                "date": (release_date - timedelta(weeks=2)).strftime("%Y-%m-%d"),
                "milestone": "Artist approval via Comms Agent",
                "owner": "comms → artist",
            },
            "t_minus_1_week": {
                "date": (release_date - timedelta(weeks=1)).strftime("%Y-%m-%d"),
                "milestone": "Store listings ready (hidden/scheduled)",
                "owner": "merch",
            },
            "t_0": {
                "date": release_date.strftime("%Y-%m-%d"),
                "milestone": "Go live with music release",
                "owner": "merch + distribution",
            },
        }

        # Kick off design brief immediately
        await self.send_message("creative", "create_merch_brief", {
            "artist_id": artist_id,
            "release_id": release_id,
            "products": products,
            "deadline": (release_date - timedelta(weeks=3)).strftime("%Y-%m-%d"),
        })

        return {
            "artist_id": artist_id,
            "release_id": release_id,
            "priority": priority,
            "products_planned": products,
            "timeline": timeline,
            "release_date": release_date.strftime("%Y-%m-%d"),
            "status": "planned",
        }

    # ----------------------------------------------------------------
    # create_product_listing
    # ----------------------------------------------------------------

    async def _create_product_listing(self, task: AgentTask) -> dict:
        p = task.payload
        artist_id = p.get("artist_id") or task.artist_id
        product_type = p.get("product_type", "t-shirt")
        name = p.get("name") or f"ECHO x Artist — {product_type.title()}"
        price = float(p.get("price") or PRICING.get(product_type, (25.0, 35.0))[0])
        cost = float(p.get("cost") or price * COST_ESTIMATES.get(product_type, 0.40))
        margin_pct = round((price - cost) / price * 100, 2) if price > 0 else 0.0

        sku = f"ECHO-{(artist_id or 'XXX')[:6].upper()}-{product_type[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"

        product_id = str(uuid.uuid4())
        await self.db_execute(
            """
            INSERT INTO merch_products
              (id, artist_id, name, product_type, sku, price, cost, margin_pct, status)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, 'draft')
            """,
            product_id,
            artist_id,
            name,
            product_type,
            sku,
            price,
            cost,
            margin_pct,
        )

        # Shopify-compatible listing structure
        shopify_data = {
            "title": name,
            "product_type": product_type,
            "vendor": "ECHO",
            "status": "draft",
            "variants": [
                {"sku": sku, "price": f"{price:.2f}", "requires_shipping": product_type != "sticker"},
            ],
            "tags": ["echo", "music-merch", product_type],
        }

        await self.log_audit("product_listing_created", "merch_products", product_id, {
            "artist_id": artist_id,
            "product_type": product_type,
        })

        return {
            "product_id": product_id,
            "artist_id": artist_id,
            "name": name,
            "product_type": product_type,
            "sku": sku,
            "price": price,
            "cost": cost,
            "margin_pct": margin_pct,
            "shopify_data": shopify_data,
            "status": "draft",
        }

    # ----------------------------------------------------------------
    # process_order
    # ----------------------------------------------------------------

    async def _process_order(self, task: AgentTask) -> dict:
        p = task.payload
        order_id = p.get("order_id") or str(uuid.uuid4())
        product_id = p.get("product_id")
        quantity = int(p.get("quantity", 1))
        customer_email = p.get("customer_email", "")
        total_amount = float(p.get("total_amount", 0.0))

        if product_id:
            # Decrement inventory
            await self.db_execute(
                "UPDATE merch_products SET inventory = GREATEST(0, inventory - $2) WHERE id = $1::uuid",
                product_id,
                quantity,
            )

            # Check if reorder needed
            product = await self.db_fetchrow(
                "SELECT inventory, name, artist_id FROM merch_products WHERE id = $1::uuid", product_id
            )
            if product and int(product.get("inventory", 0)) <= REORDER_POINT:
                logger.warning(f"[Merch] Low stock: {product.get('name')} — {product.get('inventory')} units remaining")

        await self.log_audit("order_processed", "merch_products", product_id, {
            "order_id": order_id,
            "quantity": quantity,
            "total_amount": total_amount,
            "customer_email": customer_email,
        })

        logger.info(f"[Merch] Order {order_id}: {quantity}x product {product_id} (${total_amount:.2f})")

        return {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "total_amount": total_amount,
            "fulfillment_status": "pending",
            "tracking_number": None,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    # ----------------------------------------------------------------
    # track_inventory
    # ----------------------------------------------------------------

    async def _track_inventory(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id

        if artist_id:
            products = await self.db_fetch(
                "SELECT id, name, product_type, sku, inventory, status FROM merch_products WHERE artist_id = $1::uuid ORDER BY name",
                artist_id,
            )
        else:
            products = await self.db_fetch(
                "SELECT id, name, product_type, sku, inventory, status FROM merch_products ORDER BY artist_id, name LIMIT 100"
            )

        low_stock = [p for p in products if int(p.get("inventory", 0)) <= REORDER_POINT and p.get("status") == "active"]
        out_of_stock = [p for p in products if int(p.get("inventory", 0)) == 0 and p.get("status") == "active"]

        if out_of_stock:
            logger.warning(f"[Merch] {len(out_of_stock)} products out of stock")

        return {
            "artist_id": artist_id,
            "products": products,
            "total_products": len(products),
            "low_stock_alerts": low_stock,
            "out_of_stock": out_of_stock,
            "reorder_point": REORDER_POINT,
        }

    # ----------------------------------------------------------------
    # generate_design_brief
    # ----------------------------------------------------------------

    async def _generate_design_brief(self, task: AgentTask) -> dict:
        p = task.payload
        artist_id = p.get("artist_id") or task.artist_id
        release_id = p.get("release_id") or task.release_id
        artwork_url = p.get("artwork_url", "")
        products = p.get("products", ["t-shirt", "hoodie"])
        deadline = p.get("deadline")

        # Pull artist info for context
        artist = None
        if artist_id:
            artist = await self.db_fetchrow("SELECT name, genre FROM artists WHERE id = $1::uuid", artist_id)

        artist_name = (artist.get("name") if artist else None) or "Artist"
        genre = (artist.get("genre") if artist else None) or ""

        brief = {
            "title": f"Merch Drop Design Brief — {artist_name}",
            "artist_name": artist_name,
            "genre": genre,
            "release_id": release_id,
            "products_to_design": products,
            "source_artwork_url": artwork_url,
            "brand_palette": {
                "primary": "#8b5cf6",
                "accent": "#10b981",
                "background": "#0a0a0f",
                "text": "#f9fafb",
            },
            "design_direction": (
                f"Create merch designs for {artist_name} ({genre}) that extend the visual identity "
                f"from the release artwork. Designs should feel premium and wearable — "
                f"not overly branded. Think streetwear meets music culture."
            ),
            "specs": {
                "t-shirt": "Front chest print 10\", back full print optional. PNG/AI at 300dpi.",
                "hoodie": "Front pocket print or full chest. Kangaroo pocket logo. PNG/AI at 300dpi.",
                "hat": "Embroidery-ready vector. Max 3 colors. 3\" x 1.5\" cap front.",
                "sticker": "Die-cut, 3\" diameter, CMYK at 300dpi. Outdoor vinyl.",
                "poster": "18x24\" at 300dpi. CMYK. Premium matte finish.",
                "vinyl": "12\" album artwork adaptation. Include inner sleeve design.",
            },
            "deliverables": [
                "High-res design files (AI/PSD)",
                "Print-ready exports (PNG/PDF)",
                "Mockup previews (3 angles per product)",
            ],
            "deadline": deadline,
        }

        # Forward to Creative Agent
        await self.send_message("creative", "design_merch", {
            "brief": brief,
            "artist_id": artist_id,
            "release_id": release_id,
        })

        return {
            "brief": brief,
            "artist_id": artist_id,
            "release_id": release_id,
            "sent_to_creative": True,
        }

    # ----------------------------------------------------------------
    # calculate_margins
    # ----------------------------------------------------------------

    async def _calculate_margins(self, task: AgentTask) -> dict:
        p = task.payload
        product_type = p.get("product_type", "t-shirt")
        retail_price = float(p.get("retail_price") or PRICING.get(product_type, (30.0, 30.0))[0])
        cost = float(p.get("cost") or retail_price * COST_ESTIMATES.get(product_type, 0.40))
        model = p.get("model", "pod")

        gross_margin = retail_price - cost
        margin_pct = (gross_margin / retail_price * 100) if retail_price > 0 else 0.0

        target_min, target_max = MARGIN_TARGETS.get(model, (0.40, 0.60))
        target_min_pct = target_min * 100
        target_max_pct = target_max * 100

        status = "on_target" if target_min_pct <= margin_pct <= target_max_pct else (
            "below_target" if margin_pct < target_min_pct else "above_target"
        )

        # Suggest price to hit target midpoint
        target_mid = (target_min + target_max) / 2
        suggested_price = round(cost / (1 - target_mid), 2) if (1 - target_mid) > 0 else retail_price

        return {
            "product_type": product_type,
            "model": model,
            "retail_price": retail_price,
            "cost": cost,
            "gross_margin_usd": round(gross_margin, 2),
            "margin_pct": round(margin_pct, 1),
            "target_range_pct": f"{target_min_pct:.0f}–{target_max_pct:.0f}%",
            "status": status,
            "suggested_price": suggested_price,
        }

    # ----------------------------------------------------------------
    # Legacy handlers
    # ----------------------------------------------------------------

    async def _launch_store(self, task: AgentTask) -> dict:
        artist_id = task.payload.get("artist_id") or task.artist_id
        store_url = f"https://echo.store/{(artist_id or 'new')[:8]}"
        return {"artist_id": artist_id, "store_url": store_url, "status": "live"}

    async def _merch_report(self, task: AgentTask) -> dict:
        stats = await self.db_fetchrow(
            "SELECT COUNT(*) as total_products, COALESCE(SUM(inventory), 0) as total_inventory FROM merch_products"
        )
        return {
            "total_products": int(stats.get("total_products") or 0) if stats else 0,
            "total_inventory": int(stats.get("total_inventory") or 0) if stats else 0,
            "total_sales_usd": 0.0,
            "units_sold": 0,
        }

    async def on_start(self):
        await self.broadcast("agent.status", {"agent": self.agent_id, "status": "online"})
        logger.info("[Merch] Online — managing merch drops and fulfillment")
