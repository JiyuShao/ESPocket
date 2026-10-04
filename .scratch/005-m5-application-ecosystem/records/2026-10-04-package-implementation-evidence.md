# 2026-10-04 Package implementation evidence

## 已完成实现

- Core 0.8.4 锁定补丁提供唯一 Runtime package inspect/install gate：不可变 candidate、artifact/member/path/compatibility 验证、事务 staging、pending/committed receipt、更新 backup/rollback、重启恢复、启动时重验与 built-in 精确成员 allowlist。
- Receipt 显式持久化 package/version、artifact digest、manifest digest、signing-key identity、policy/platform、member map、transaction identity，并分别记录 unsigned 与 `super` 例外。Unsigned identity 为 `unverified`；signed identity 绑定实际 PEM 字节 SHA-256。
- `SystemApi` inspect/install 恢复 native-system App 授权；self-replacement 检查将已观察 artifact SHA 绑定到最终 Core install，避免路径换包。
- 更新使用 Core replacement detach，不触发 ordinary uninstall/AppUninstalled。ESPocket 以 `CardRegistry::update_app()` 更新声明，清理旧 AppId navigation/runtime/factory state；失败回滚重新注册旧版本并恢复 Card 声明，保留 private data。
- 启动恢复会移除首次安装中断留下的 pending-only final 和 `.installing`，但不删除 committed final。Developer Mode 关闭时 Core 尝试停止所有依赖例外的运行实例，并在处理完后报告首个错误。
- Store 在 Core inspect 后捕获 SHA/ID/version；Developer compatibility prompt 区分 `super` 与 unsigned publisher warning。Cancel、dialog replacement/show failure、生命周期 generation 变化都会清除 pending confirmation；确认后仍由 Core 对私有 snapshot 重验。
- 外部、已准入、依赖 Developer Mode 的旧包可以缺少 `navigation.json`；不创建 Page adapter，navigation request 返回 `page_adapter_unavailable`。USB 命令范围未扩展，无法提供确认时正常拒绝例外包。

## 自动验证

- `python3 firmware/test/host/test_runtime_package_admission.py`：通过。测试实际应用 patch、编译 patched Core package/transaction 代码，覆盖 normal/developer、espocket/super/other、unsigned/半套/无效签名、digest/member/path、pending/committed receipt、显式 receipt identity、更新注入失败、private data、首次安装 pending/orphan cleanup、rollback recovery 与 built-in allowlist。
- `PYTHON_COLORS=0 NO_COLOR=1 python3 scripts/check.py`：80 项 host tests 全部通过；Markdown 检查同时通过（262 files）。
- Core 与 Store patch manifest 均通过 `prepare_patched_component.py` 精确输入、hash、顺序及应用检查。
- `git diff --check`：通过。

## 未完成与阻塞

- 完整 patched firmware 构建尝试两次，均未得到镜像。第一次在 Component Manager 复制 `esp-sr` 时因磁盘空间不足失败；清理本次 scratch 后第二次仍仅有约 1.1 GiB 可用，并在依赖物化期间耗尽。失败不是 firmware compile 结果，不能记录为构建通过。
- 因没有最终镜像，未进行 app/LittleFS 备份、app-only flash 或真机 Store Cancel/install/start/PWR/reboot/mode-off/re-enable/update rollback 验收。没有刷写设备。
- 设备 full-flash backup 可能包含 credentials/personal data，先前被权限策略拒绝。后续应按 Handoff 仅备份 app partition (`0x60000..0xaa1000`) 与 LittleFS (`0xaa1000`, `0x4e2000`)，并由用户明确授权保存范围后再刷写。
- Ticket 08 尚未配置正式 release key；product 对 signed external package 保持 fail closed。当前只证明无效/半套 signature 不降级，不能声称正式签名发行验收。
- Ticket 04 dynamic Launcher 不在本次授权范围；当前产品没有任意新装 external App 的稳定可见启动入口，因此 09 的实际 launch/device matrix 仍需 04 或另一个已授权原生入口。

## 下一验收入口

释放至少数 GiB 磁盘空间后，以新 outside-checkout workspace 重跑：

```sh
source "$HOME/.espressif/v6.0.1/esp-idf/export.sh"
python3 scripts/firmware/build_patched_firmware.py \
  --workspace /private/tmp/espocket-m5-package-final \
  --sdkconfig firmware/sdkconfig \
  --patch-set production
```

构建成功后保留 `patch-inputs.json`、registry lock、sdkconfig、ELF/BIN SHA-256 与 build log；获得备份授权后再执行 app-only 设备验收，禁止写入构建产出的 LittleFS。
