"""
AutoPrice AI - Main FastAPI Application
Autonomous Pricing Analyst Agent Backend
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import AGENT_LOOP_INTERVAL
from database.db import init_db
from database.seed import seed_database
from database.models import Product, PriceHistory, AgentLog, Decision, Notification
from database.db import get_db_session
from websocket_manager import ws_manager
from agents.orchestrator import OrchestratorAgent
from tools.product_tools import get_product_data, get_price_history
from tools.explanation_tools import get_recent_decisions, get_agent_activity
from tools.notification_tools import get_notifications, mark_notification_read, send_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize orchestrator
orchestrator = OrchestratorAgent()
agent_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    global agent_task

    # Startup
    logger.info("Starting AutoPrice AI...")
    init_db()
    seed_database()

    # Set broadcast function for orchestrator
    orchestrator.set_broadcast(ws_manager.broadcast)

    # Start autonomous agent loop
    agent_task = asyncio.create_task(orchestrator.start_loop(interval=AGENT_LOOP_INTERVAL))
    logger.info(f"Agent loop started with {AGENT_LOOP_INTERVAL}s interval")

    yield

    # Shutdown
    logger.info("Shutting down AutoPrice AI...")
    orchestrator.stop_loop()
    if agent_task:
        agent_task.cancel()
        try:
            await agent_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="AutoPrice AI",
    description="Autonomous Pricing Analyst Agent - Enterprise E-commerce Pricing Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== WebSocket Endpoint =====
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle incoming messages
            data = await websocket.receive_text()
            # Echo back acknowledgement
            await ws_manager.send_personal(websocket, {"type": "ack", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ===== API Endpoints =====

@app.get("/")
async def root():
    """Health check"""
    return {"status": "running", "service": "AutoPrice AI", "version": "1.0.0"}


@app.get("/api/products")
async def get_products():
    """Get all active products with pricing data"""
    try:
        products = get_product_data()
        return {"success": True, "products": products, "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    """Get a single product by ID"""
    try:
        products = get_product_data(product_id)
        if not products:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"success": True, "product": products[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}/history")
async def get_product_history(product_id: int, limit: int = 20):
    """Get price history for a product"""
    try:
        history = get_price_history(product_id, limit)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/decisions")
async def get_decisions(limit: int = 30):
    """Get recent pricing decisions"""
    try:
        decisions = get_recent_decisions(limit)
        return {"success": True, "decisions": decisions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-activity")
async def get_activity(limit: int = 50):
    """Get recent agent activity"""
    try:
        activity = get_agent_activity(limit)
        return {"success": True, "activity": activity}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/notifications")
async def get_all_notifications(limit: int = 20, unread_only: bool = False):
    """Get notifications"""
    try:
        notifications = get_notifications(limit, unread_only)
        return {"success": True, "notifications": notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notifications/{notification_id}/read")
async def read_notification(notification_id: int):
    """Mark notification as read"""
    try:
        result = mark_notification_read(notification_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-status")
async def get_agent_status():
    """Get current agent system status"""
    try:
        status = orchestrator.get_status()
        return {"success": True, **status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard summary statistics"""
    db = get_db_session()
    try:
        total_products = db.query(Product).filter(Product.is_active == True).count()
        total_decisions = db.query(Decision).count()
        
        products = db.query(Product).filter(Product.is_active == True).all()
        
        total_revenue = sum(p.our_price * max(1, p.stock // 10) for p in products)
        avg_margin = sum(
            ((p.our_price - p.cost_price) / p.our_price) * 100 
            for p in products
        ) / max(1, len(products))

        products_below_competitor = sum(
            1 for p in products if p.our_price < p.competitor_price
        )

        return {
            "success": True,
            "stats": {
                "total_products": total_products,
                "total_decisions": total_decisions,
                "total_cycles": orchestrator.memory_agent.cycle_count,
                "total_updates": orchestrator.memory_agent.total_updates,
                "avg_margin": round(avg_margin, 1),
                "products_below_competitor": products_below_competitor,
                "agent_running": orchestrator.is_running
            }
        }
    finally:
        db.close()


@app.get("/api/analytics/price-trends")
async def get_price_trends():
    """Get aggregated price trend data for charts"""
    db = get_db_session()
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta

        # Get last 20 price history entries per product
        products = db.query(Product).filter(Product.is_active == True).all()
        trends = {}

        for product in products:
            history = db.query(PriceHistory).filter(
                PriceHistory.product_id == product.id
            ).order_by(PriceHistory.timestamp.asc()).limit(20).all()

            trends[product.id] = {
                "name": product.name,
                "data": [{
                    "timestamp": h.timestamp.isoformat(),
                    "our_price": h.new_price,
                    "competitor_price": h.competitor_price,
                    "profit_margin": h.profit_margin
                } for h in history]
            }

        return {"success": True, "trends": trends}
    finally:
        db.close()


@app.post("/api/products/{product_id}/competitor-price")
async def update_competitor_price(product_id: int, body: dict):
    """
    Manually update competitor price for demo purposes.
    The agent will detect this change on the next cycle and adjust our price.
    """
    db = get_db_session()
    try:
        new_price = body.get("competitor_price")
        if not new_price or new_price <= 0:
            raise HTTPException(status_code=400, detail="Invalid competitor price")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        old_competitor_price = product.competitor_price
        product.competitor_price = float(new_price)
        db.commit()

        # Broadcast the manual change to frontend
        await ws_manager.broadcast({
            "type": "competitor_update",
            "product_id": product_id,
            "product_name": product.name,
            "old_competitor_price": old_competitor_price,
            "new_competitor_price": float(new_price)
        })

        # Trigger immediate agent processing for this product
        asyncio.create_task(orchestrator.process_product(product_id))

        return {
            "success": True,
            "product_id": product_id,
            "old_competitor_price": old_competitor_price,
            "new_competitor_price": float(new_price),
            "message": "Competitor price updated. Agent will respond shortly."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/decisions/{decision_id}/undo")
async def undo_decision(decision_id: int):
    """Undo a pricing decision - revert product price to old_price"""
    db = get_db_session()
    try:
        decision = db.query(Decision).filter(Decision.id == decision_id).first()
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        product = db.query(Product).filter(Product.id == decision.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        reverted_from = product.our_price
        product.our_price = decision.old_price
        product.updated_at = datetime.utcnow()

        # Log the undo as a new price history entry
        from database.models import PriceHistory as PH
        ph = PH(
            product_id=product.id,
            old_price=reverted_from,
            new_price=decision.old_price,
            competitor_price=product.competitor_price,
            reason=f"Manual undo of decision #{decision_id} by admin",
            agent_name="Admin",
            profit_margin=((decision.old_price - product.cost_price) / decision.old_price) * 100,
        )
        db.add(ph)

        # Log agent activity for the undo
        undo_log = AgentLog(
            agent_name="Admin",
            action=f"Undo decision #{decision_id} for {product.name}",
            details=f"Reverted price from ₹{reverted_from:,.0f} to ₹{decision.old_price:,.0f}",
            status="completed",
            product_id=product.id,
        )
        db.add(undo_log)

        db.commit()

        # Broadcast the revert
        await ws_manager.broadcast({
            "type": "price_update",
            "product_id": product.id,
            "product_name": product.name,
            "old_price": reverted_from,
            "new_price": decision.old_price,
            "decision_type": "undo",
            "change_percentage": ((decision.old_price - reverted_from) / reverted_from) * 100,
        })

        # Send email notification for the undo
        send_notification(
            product_id=product.id,
            title=f"Price Reverted: {product.name}",
            message=(
                f"Admin manually reverted price for {product.name} from "
                f"₹{reverted_from:,.0f} back to ₹{decision.old_price:,.0f}. "
                f"Decision #{decision_id} has been undone."
            ),
            notification_type="warning",
        )

        return {
            "success": True,
            "product_id": product.id,
            "reverted_from": reverted_from,
            "reverted_to": decision.old_price,
            "message": f"Price for {product.name} reverted to ₹{decision.old_price:,.0f}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/decisions/with-logs")
async def get_decisions_with_logs(limit: int = 50):
    """Get recent decisions with associated agent logs for the Agents Update page"""
    db = get_db_session()
    try:
        decisions = db.query(Decision).order_by(Decision.timestamp.desc()).limit(limit).all()
        result = []
        for d in decisions:
            # Get agent logs around the decision timestamp (within 30 seconds)
            from datetime import timedelta
            start = d.timestamp - timedelta(seconds=30)
            end = d.timestamp + timedelta(seconds=5)
            logs = db.query(AgentLog).filter(
                AgentLog.product_id == d.product_id,
                AgentLog.timestamp >= start,
                AgentLog.timestamp <= end,
            ).order_by(AgentLog.timestamp.asc()).all()

            product = db.query(Product).filter(Product.id == d.product_id).first()

            result.append({
                "id": d.id,
                "product_id": d.product_id,
                "product_name": d.product_name,
                "decision_type": d.decision_type,
                "old_price": d.old_price,
                "new_price": d.new_price,
                "competitor_price": d.competitor_price,
                "reason": d.reason,
                "confidence": d.confidence,
                "profit_impact": d.profit_impact,
                "agent_chain": json.loads(d.agent_chain) if d.agent_chain else [],
                "timestamp": d.timestamp.isoformat(),
                "current_price": product.our_price if product else d.new_price,
                "can_undo": product.our_price == d.new_price if product else False,
                "logs": [{
                    "id": l.id,
                    "agent_name": l.agent_name,
                    "action": l.action,
                    "details": l.details,
                    "status": l.status,
                    "timestamp": l.timestamp.isoformat(),
                } for l in logs],
            })

        # KPIs
        from sqlalchemy import func
        total_updates = db.query(Decision).filter(Decision.decision_type != "no_change").count()
        total_increases = db.query(Decision).filter(Decision.decision_type == "price_increase").count()
        total_decreases = db.query(Decision).filter(Decision.decision_type == "price_decrease").count()
        avg_confidence = db.query(func.avg(Decision.confidence)).scalar() or 0

        return {
            "success": True,
            "decisions": result,
            "kpis": {
                "total_decisions": db.query(Decision).count(),
                "total_updates": total_updates,
                "total_increases": total_increases,
                "total_decreases": total_decreases,
                "avg_confidence": round(float(avg_confidence) * 100, 1),
                "no_change_count": db.query(Decision).filter(Decision.decision_type == "no_change").count(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/api/trigger-cycle")
async def trigger_cycle():
    """Manually trigger an agent cycle for demo"""
    try:
        result = await orchestrator.run_cycle()
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
