from flask import Flask, request, render_template, jsonify, send_file
from zep_cloud.client import Zep
import os
import json
from dotenv import load_dotenv
from pyvis.network import Network
from flask_cors import CORS

# === 加载配置 ===
load_dotenv()
API_KEY = os.environ.get("ZEP_API_KEY")
client = Zep(api_key=API_KEY)

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])


# === 首页页面 ===
@app.route("/")
def index():
    return render_template("index.html")


# === 创建项目接口 ===
@app.route("/create_project", methods=["POST"])
def create_project():
    try:
        # 从前端表单或 JSON 取出项目名（作为 user_id）
        project_name = request.form.get("project_name") or request.json.get("project_name")
        if not project_name:
            return jsonify({"status": "error", "message": "Missing project name"}), 400

        user_id = project_name  # 用项目名作为 user_id

        # 可以自定义项目的 email/first_name/last_name，这里简单生成
        new_user = client.user.add(
            user_id=user_id,
            email=f"{user_id}@auto.project",
            first_name=project_name,
            last_name="Project"
        )

        return jsonify({"status": "success", "message": f"Project '{project_name}' created.", "user_id": user_id})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# === 提交摘要接口 ===
@app.route("/submitsummary", methods=["POST"])
def submit_summary():
    try:
        project_name = request.form.get("project_name")
        article_title = request.form.get("article_title")
        chapter = request.form.get("chapter")
        description = request.form.get("summary")

        if not all([project_name, article_title, description]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        summary = {
            "content": {
                "project_name": project_name,
                "article_title": article_title,
                "summary": description,
                "chapter": chapter or ""
            }
        }

        json_data = json.dumps(summary["content"], ensure_ascii=False)

        res = client.graph.add(
            user_id=project_name,  # 用 project_name 作为 user_id
            type="json",
            data=json_data
        )
        return jsonify({"status": "success", "message": "Summary added successfully!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# === 提交笔记接口 ===
@app.route("/submitnote", methods=["POST"])
def submit_note():
    try:
        project_name = request.form.get("project_name")
        article_title = request.form.get("article_title")
        origin = request.form.get("origin")
        comment = request.form.get("comment")

        if not all([project_name, article_title, origin]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        note = {
            "content": {
                "project_name": project_name,
                "article_title": article_title,
                "origin": origin,
                "comment": comment or ""
            }
        }

        json_data = json.dumps(note["content"], ensure_ascii=False)

        res = client.graph.add(
            user_id=project_name,  # 用 project_name 作为 user_id
            type="json",
            data=json_data
        )
        return jsonify({"status": "success", "message": "Note added successfully!"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# @app.route("/graph")
# def generate_graph():
#     user_id = request.args.get("user_id")
#     if not user_id:
#         return "Missing user_id (project_name)", 400

#     try:
#         nodes = client.graph.node.get_by_user_id(user_id)
#         edges = client.graph.edge.get_by_user_id(user_id)

#         net = Network(height='1000px', width='100%', directed=True)

#         for node in nodes:
#             label = node.name or "no name"
#             net.add_node(node.uuid_, label=label, title=node.summary or "")

#         for edge in edges:
#             src = edge.source_node_uuid
#             tgt = edge.target_node_uuid
#             label = edge.name or "relation"
#             net.add_edge(src, tgt, label=label, title=edge.fact or "")

#         net.set_options("""var options = {
#           "physics": {
#             "enabled": true,
#             "stabilization": {
#               "enabled": true,
#               "iterations": 200
#             },
#             "forceAtlas2Based": {
#               "gravitationalConstant": -50,
#               "centralGravity": 0.01,
#               "springLength": 120,
#               "springConstant": 0.08,
#               "damping": 0.4,
#               "avoidOverlap": 1
#             },
#             "minVelocity": 0.75,
#             "solver": "forceAtlas2Based"
#           }
#         }""")

#         # 添加交互事件
#         net.html += """
#         <script type="text/javascript">
#             // 等待图加载完成
#             network.on("click", function (params) {
#                 if (params.nodes.length > 0) {
#                     let nodeId = params.nodes[0];
#                     let nodeData = nodes.get(nodeId);
#                     alert("你点击了节点：" + nodeData.label);
#                     // 你可以在这里发起 AJAX 请求加载更多信息，或跳转链接等
#                     // 例如 fetch(`/node_detail?uuid=${nodeId}`).then(...)
#                 }
#             });
#         </script>
#         """

#         graph_path = f"static/graph_output_{user_id}.html"
#         net.write_html(graph_path)
#         return send_file(graph_path)

#     except Exception as e:
#         return f"图谱生成失败：{str(e)}", 500
@app.route("/graph_data")
def graph_data():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400

    try:
        nodes = client.graph.node.get_by_user_id(user_id)
        edges = client.graph.edge.get_by_user_id(user_id)

        node_list = [{
            "id": node.uuid_,
            "label": node.name or "no name",
            "title": node.summary or "",
            "created_at": node.created_at
        } for node in nodes]

        edge_list = [{
            "from": edge.source_node_uuid,
            "to": edge.target_node_uuid,
            "label": edge.name or "relation",
            "title": edge.fact or "",
        } for edge in edges]

        return jsonify({"status": "success", "nodes": node_list, "edges": edge_list})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/node_episodes")
def get_node_episodes():
    node_uuid = request.args.get("node_uuid")
    if not node_uuid:
        return jsonify({"status": "error", "message": "Missing node_uuid"}), 400

    try:
        episodes = client.graph.node.get_episodes(node_uuid=node_uuid).episodes  

        episode_list = []
        for ep in episodes:
            try:
                content = json.loads(ep.content)
                is_note = "origin" in content or "comment" in content
                is_summary = "summary" in content

                if is_note:
                    episode_list.append({
                        "type": "note",
                        "article_title": content.get("article_title", "(无标题)"),
                        "origin": content.get("origin", ""),
                        "comment": content.get("comment", "（无笔记）"),
                        "created_at": ep.created_at,
                        "uuid": getattr(ep, "uuid", None)
                    })
                elif is_summary:
                    episode_list.append({
                        "type": "summary",
                        "article_title": content.get("article_title", "(无标题)"),
                        "summary": content.get("summary", ""),
                        "chapter": content.get("chapter", "（无章节信息）"),
                        "created_at": ep.created_at,
                        "uuid": getattr(ep, "uuid", None)
                    })
                else:
                    print(f"[跳过] 无有效字段: {content}")
            except Exception as e:
                print(f"[跳过] JSON 解析失败: {e}")

        return jsonify({"status": "success", "episodes": episode_list})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500




@app.route("/search", methods=["POST"])
def search_nodes_or_episodes():
    try:
        query = request.form.get("query")
        project_name = request.form.get("project_name")
        scope = request.form.get("scope", "nodes")  # 默认搜 nodes
        if not query:
            return jsonify({"status": "error", "message": "Missing search query"}), 400

        search_results = client.graph.search(
            user_id=project_name,
            query=query,
            scope=scope,
            limit=3,
        )

        result_list = []
        if scope == "nodes":
            for idx, node in enumerate(search_results.nodes, start=1):
                result_list.append({
                    "type": "node",
                    "index": idx,
                    "name": node.name,
                    "summary": node.summary,
                    "created_at": node.created_at,
                })
        elif scope == "episodes":
            for idx, ep in enumerate(search_results.episodes, start=1):
                content = json.loads(ep.content)
                result_list.append({
                    "type": "episode",
                    "index": idx,
                    "project_name": content.get("project_name", ""),
                    "article_title": content.get("article_title", ""),
                    "origin": content.get("origin", ""),
                    "comment": content.get("comment", ""),
                    "created_at": ep.created_at,
                })

        return jsonify({"status": "success", "results": result_list})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5001, debug=True)