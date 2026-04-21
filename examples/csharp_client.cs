using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

class Program
{
    static readonly string BaseUrl = "http://127.0.0.1:8000";
    static readonly string ApiKey = "";

    static async Task<string> PostJson(string path, string json)
    {
        using (var client = new HttpClient())
        {
            if (!string.IsNullOrEmpty(ApiKey))
            {
                client.DefaultRequestHeaders.Add("X-API-Key", ApiKey);
            }

            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await client.PostAsync(BaseUrl + path, content);
            return await response.Content.ReadAsStringAsync();
        }
    }

    static async Task Main()
    {
        string json = "{" +
            "\"agent_id\":\"bot_cs_001\"," +
            "\"tick\":1," +
            "\"state\":{" +
            "\"hp\":90," +
            "\"mp\":30," +
            "\"x\":10," +
            "\"y\":20," +
            "\"map_id\":1," +
            "\"heading\":0," +
            "\"target_id\":\"mob_1\"," +
            "\"target_distance\":1," +
            "\"target_hp\":60," +
            "\"is_under_attack\":false," +
            "\"nearby_enemies\":1," +
            "\"nearby_allies\":0," +
            "\"safe_zone\":false," +
            "\"can_teleport\":false," +
            "\"weight_percent\":20," +
            "\"cooldowns\":{}," +
            "\"inventory\":{}," +
            "\"buffs\":[]," +
            "\"debuffs\":[]," +
            "\"aggro_targets\":[]," +
            "\"extras\":{}" +
            "}}";

        Console.WriteLine(await PostJson("/observe", json));
        Console.WriteLine(await PostJson("/decide", json));
    }
}
