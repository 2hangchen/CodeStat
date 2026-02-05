"""统一入口：支持启动服务器或CLI"""
import argparse
import sys


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="本地MCP Server AI代码统计系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s server start          # 启动MCP服务器
  %(prog)s server start --port 8080  # 指定端口启动服务器
  %(prog)s cli                    # 启动交互式CLI
  %(prog)s cli --session <id>     # 快捷查询会话
  %(prog)s cli --file <path>      # 快捷查询文件
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # Server子命令
    server_parser = subparsers.add_parser('server', help='启动MCP服务器')
    server_parser.add_argument(
        'action',
        choices=['start'],
        help='启动服务器'
    )
    server_parser.add_argument(
        '--host',
        type=str,
        help='服务器监听地址（默认从config.json读取）'
    )
    server_parser.add_argument(
        '--port',
        type=int,
        help='服务器监听端口（默认从config.json读取）'
    )
    server_parser.add_argument(
        '--daemon',
        action='store_true',
        help='后台运行'
    )
    
    # CLI子命令
    cli_parser = subparsers.add_parser('cli', help='启动交互式CLI')
    cli_parser.add_argument(
        '--session',
        type=str,
        help='按会话ID查询（快捷命令）'
    )
    cli_parser.add_argument(
        '--file',
        type=str,
        help='按文件路径查询（快捷命令）'
    )
    cli_parser.add_argument(
        '--project',
        type=str,
        help='按项目根目录查询（快捷命令）'
    )
    cli_parser.add_argument(
        '--export',
        type=str,
        choices=['json', 'csv'],
        help='导出格式（需配合--session/--file/--project使用）'
    )
    cli_parser.add_argument(
        '--output',
        type=str,
        help='导出文件路径（需配合--export使用）'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'server':
        # 启动服务器
        if args.action == 'start':
            import uvicorn
            import logging
            from config import get_server_config
            from logging_config import setup_logging
            from storage.db import get_db
            from storage.scheduler import start_scheduler
            from local_mcp_server import app
            
            logger = setup_logging(log_level="INFO", module_name="mcp_server")
            
            # 初始化数据库
            try:
                db = get_db()
                db.initialize()
                logger.info("Database initialized successfully")
                start_scheduler()
                logger.info("Scheduler started (auto backup and cleanup)")
            except Exception as e:
                logger.error(f"Failed to initialize: {e}")
                sys.exit(1)
            
            # 获取配置
            server_config = get_server_config()
            host = args.host or server_config["host"]
            preferred_port = args.port or server_config["port"]
            log_level = server_config.get("log_level", "info")
            
            # 检查端口是否可用，如果被占用则选择随机端口
            from utils.port_utils import find_available_port
            try:
                port = find_available_port(host, preferred_port)
                if port != preferred_port:
                    logger.warning(f"Port {preferred_port} is in use, using port {port} instead")
            except RuntimeError as e:
                logger.error(f"Failed to find available port: {e}")
                sys.exit(1)
            
            logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
            logger.info(f"Starting MCP Server on {host}:{port}")
            logger.info("MCP Tools available at:")
            logger.info(f"  GET  http://{host}:{port}/mcp/tools (Tool discovery)")
            logger.info(f"  POST http://{host}:{port}/mcp/record_before")
            logger.info(f"  POST http://{host}:{port}/mcp/record_after")
            
            if args.daemon:
                logger.warning("Daemon mode is a simple implementation. For production, use systemd/supervisor/nohup.")
                import multiprocessing
                
                def run_server():
                    uvicorn.run(app, host=host, port=port, log_level=log_level)
                
                process = multiprocessing.Process(target=run_server, daemon=True)
                process.start()
                logger.info(f"Server started in background (PID: {process.pid})")
                logger.info("To stop the server, use: kill <PID>")
            else:
                uvicorn.run(app, host=host, port=port, log_level=log_level)
    
    elif args.command == 'cli':
        # 启动CLI
        from cli.main import main as cli_main
        # 设置快捷命令参数
        if args.session or args.file or args.project:
            # 快捷命令模式，需要重新设置sys.argv
            sys.argv = ['cli/main.py']
            if args.session:
                sys.argv.extend(['--session', args.session])
            if args.file:
                sys.argv.extend(['--file', args.file])
            if args.project:
                sys.argv.extend(['--project', args.project])
            if args.export:
                sys.argv.extend(['--export', args.export])
            if args.output:
                sys.argv.extend(['--output', args.output])
        cli_main()


if __name__ == '__main__':
    main()

