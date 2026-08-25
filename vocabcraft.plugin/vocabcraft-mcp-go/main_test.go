package main

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"testing"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func TestHandshake(t *testing.T) {
	exe := filepath.Join("cmd", "vocabcraft-mcp", "vocabcraft-mcp.exe")
	dataDir := t.TempDir()
	t.Setenv("VOCABCRAFT_DATA_DIR", dataDir)

	client := mcp.NewClient(&mcp.Implementation{Name: "test", Version: "1.0"}, nil)
	transport := &mcp.CommandTransport{Command: exec.Command(exe)}
	session, err := client.Connect(context.Background(), transport, nil)
	if err != nil {
		t.Fatalf("connect failed: %v", err)
	}
	defer session.Close()

	// List tools
	res, err := session.ListTools(context.Background(), nil)
	if err != nil {
		t.Fatalf("list tools failed: %v", err)
	}
	if len(res.Tools) == 0 {
		t.Fatal("expected tools, got 0")
	}
	t.Logf("found %d tools:", len(res.Tools))
	for _, tool := range res.Tools {
		t.Logf("  - %s: %s", tool.Name, tool.Description)
	}
}

func TestSaveAndLoadVocab(t *testing.T) {
	exe := filepath.Join("cmd", "vocabcraft-mcp", "vocabcraft-mcp.exe")
	dataDir := t.TempDir()
	t.Setenv("VOCABCRAFT_DATA_DIR", dataDir)

	client := mcp.NewClient(&mcp.Implementation{Name: "test", Version: "1.0"}, nil)
	transport := &mcp.CommandTransport{Command: exec.Command(exe)}
	session, err := client.Connect(context.Background(), transport, nil)
	if err != nil {
		t.Fatalf("connect failed: %v", err)
	}
	defer session.Close()

	// Save a vocab
	saveRes, err := session.CallTool(context.Background(), &mcp.CallToolParams{
		Name: "save_vocab",
		Arguments: map[string]any{
			"vocab_data": map[string]any{
				"structured": map[string]any{
					"word":         "hello",
					"phonetic":     "/həˈloʊ/",
					"part_of_speech": "interj.",
					"definitions": []map[string]any{
						{"text": "你好；喂", "examples": []string{"Hello, how are you?"}},
					},
					"language": "en",
				},
			},
		},
	})
	if err != nil {
		t.Fatalf("save_vocab failed: %v", err)
	}
	t.Logf("save result: %v", saveRes)

	// Query
	queryRes, err := session.CallTool(context.Background(), &mcp.CallToolParams{
		Name:      "query_vocab",
		Arguments: map[string]any{"filters": map[string]any{"language": "en"}},
	})
	if err != nil {
		t.Fatalf("query_vocab failed: %v", err)
	}
	t.Logf("query result: %v", queryRes)
	_ = os.Stdout
}
