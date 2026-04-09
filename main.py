



















# # main.py this not runing currenlty
# def main():
#     print("Hello from mcp-server-demo!")


# if __name__ == "__main__":
#     main()

# #to make it run use  hideded coad

# # main.py

# # import asyncio
# # from src.server import mcp  # adjust the path if server.py is in a different location

# # def main():
# #     print("✅ Starting MCP Server from main.py...")
# #     asyncio.run(mcp.run())

# # if __name__ == "__main__":
# #     main()


#############################################################################################################
# new coad bewlow


from server import mcp
import asyncio

def main():
    asyncio.run(mcp.run())

if __name__ == "__main__":
    main()
