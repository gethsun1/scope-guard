from scope_guard.engine import HostedDemoRunner


async def test_hosted_runner_restores_only_target_state() -> None:
    runner = HostedDemoRunner()
    before = await runner.execute("snapshot")
    await runner.execute("deploy_rdsocial")
    await runner.execute("migrate_rdsocial")
    await runner.execute("fail_rdsocial")
    final = await runner.execute("rollback_rdsocial")
    assert final["rdsocial_hash"] == before["rdsocial_hash"]
    assert final["engageflow_hash"] == before["engageflow_hash"]
    assert final["engageflow"] == {"healthy": True, "release": 1, "migration": 0}


async def test_hosted_runner_reset_is_deterministic() -> None:
    runner = HostedDemoRunner()
    baseline = await runner.execute("reset")
    await runner.execute("deploy_rdsocial")
    reset = await runner.execute("reset")
    assert reset["rdsocial_hash"] == baseline["rdsocial_hash"]
    assert reset["engageflow_hash"] == baseline["engageflow_hash"]
