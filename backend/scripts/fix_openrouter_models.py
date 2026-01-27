#!/usr/bin/env python3
"""
Script to find and update all agent_versions with openrouter/* models
to use kortix/basic or kortix/power instead.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.supabase import DBConnection
from core.utils.logger import logger
from core.ai_models.registry import FREE_MODEL_ID, PREMIUM_MODEL_ID


async def find_and_fix_openrouter_models():
    """Find all agent_versions with openrouter/* models and update them."""
    db_connection = DBConnection()
    client = await db_connection.client
    
    # Find all agent_versions with openrouter models in config
    logger.info("🔍 Searching for agent_versions with openrouter/* models...")
    
    # Query all agent_versions and check their config
    result = await client.table('agent_versions').select(
        'version_id, agent_id, config'
    ).execute()
    
    if not result.data:
        logger.info("No agent_versions found.")
        return
    
    openrouter_versions = []
    for version in result.data:
        config = version.get('config', {})
        model = config.get('model', '')
        
        if model and model.startswith('openrouter/'):
            openrouter_versions.append({
                'version_id': version['version_id'],
                'agent_id': version['agent_id'],
                'old_model': model,
                'config': config
            })
    
    if not openrouter_versions:
        logger.info("✅ No agent_versions with openrouter/* models found!")
        return
    
    logger.info(f"📋 Found {len(openrouter_versions)} agent_versions with openrouter/* models:")
    for v in openrouter_versions:
        logger.info(f"  - Version {v['version_id']}: {v['old_model']}")
    
    # Update them to use kortix/basic (default)
    logger.info(f"\n🔄 Updating {len(openrouter_versions)} agent_versions to use {FREE_MODEL_ID}...")
    
    updated_count = 0
    for v in openrouter_versions:
        try:
            # Update the config to use kortix/basic
            new_config = v['config'].copy()
            new_config['model'] = FREE_MODEL_ID
            
            # Update in database
            update_result = await client.table('agent_versions').update({
                'config': new_config
            }).eq('version_id', v['version_id']).execute()
            
            if update_result.data:
                updated_count += 1
                logger.info(f"  ✅ Updated version {v['version_id']}: {v['old_model']} → {FREE_MODEL_ID}")
            else:
                logger.warning(f"  ⚠️  Failed to update version {v['version_id']}")
        except Exception as e:
            logger.error(f"  ❌ Error updating version {v['version_id']}: {e}")
    
    logger.info(f"\n✅ Successfully updated {updated_count}/{len(openrouter_versions)} agent_versions!")
    
    # Also check agents table config
    logger.info("\n🔍 Checking agents table for openrouter/* models...")
    agents_result = await client.table('agents').select(
        'agent_id, config'
    ).execute()
    
    if agents_result.data:
        openrouter_agents = []
        for agent in agents_result.data:
            config = agent.get('config', {})
            model = config.get('model', '')
            
            if model and model.startswith('openrouter/'):
                openrouter_agents.append({
                    'agent_id': agent['agent_id'],
                    'old_model': model,
                    'config': config
                })
        
        if openrouter_agents:
            logger.info(f"📋 Found {len(openrouter_agents)} agents with openrouter/* models:")
            for a in openrouter_agents:
                logger.info(f"  - Agent {a['agent_id']}: {a['old_model']}")
            
            logger.info(f"\n🔄 Updating {len(openrouter_agents)} agents to use {FREE_MODEL_ID}...")
            
            agent_updated_count = 0
            for a in openrouter_agents:
                try:
                    new_config = a['config'].copy()
                    new_config['model'] = FREE_MODEL_ID
                    
                    update_result = await client.table('agents').update({
                        'config': new_config
                    }).eq('agent_id', a['agent_id']).execute()
                    
                    if update_result.data:
                        agent_updated_count += 1
                        logger.info(f"  ✅ Updated agent {a['agent_id']}: {a['old_model']} → {FREE_MODEL_ID}")
                except Exception as e:
                    logger.error(f"  ❌ Error updating agent {a['agent_id']}: {e}")
            
            logger.info(f"\n✅ Successfully updated {agent_updated_count}/{len(openrouter_agents)} agents!")
        else:
            logger.info("✅ No agents with openrouter/* models found!")


if __name__ == "__main__":
    asyncio.run(find_and_fix_openrouter_models())

