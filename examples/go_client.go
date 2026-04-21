package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

const baseURL = "http://127.0.0.1:8000"
const apiKey = ""

func post(path string, payload map[string]interface{}) (map[string]interface{}, error) {
    data, _ := json.Marshal(payload)
    req, _ := http.NewRequest("POST", baseURL+path, bytes.NewBuffer(data))
    req.Header.Set("Content-Type", "application/json")
    if apiKey != "" {
        req.Header.Set("X-API-Key", apiKey)
    }

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result map[string]interface{}
    err = json.NewDecoder(resp.Body).Decode(&result)
    return result, err
}

func main() {
    payload := map[string]interface{}{
        "agent_id": "bot_go_001",
        "tick": 1,
        "state": map[string]interface{}{
            "hp": 85,
            "mp": 30,
            "x": 100,
            "y": 220,
            "map_id": 1,
            "heading": 1,
            "target_id": "mob_2",
            "target_distance": 1,
            "target_hp": 75,
            "is_under_attack": true,
            "nearby_enemies": 2,
            "nearby_allies": 1,
            "safe_zone": false,
            "can_teleport": true,
            "weight_percent": 25,
            "cooldowns": map[string]interface{}{"heal": 0},
            "inventory": map[string]interface{}{"potion": 2},
            "buffs": []string{},
            "debuffs": []string{},
            "aggro_targets": []string{"mob_2"},
            "extras": map[string]interface{}{},
        },
    }

    observeRes, _ := post("/observe", payload)
    decideRes, _ := post("/decide", payload)
    fmt.Println(observeRes)
    fmt.Println(decideRes)
}
