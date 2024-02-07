🇬🇧 [English](./README.md) | 🇹🇼 [繁體中文](./README-zh-tw.md)

# 工地危險檢測

"工地危險檢測" 是一款旨在提高工地安全性的 AI 驅動工具。利用 YOLOv8 模型進行物體檢測，此系統能夠識別潛在的危險，如懸掛的重物和鋼管。對訓練好的模型進行後處理以提高準確性。該系統設計用於即時環境部署，為檢測到的任何危險提供即時分析和警告。

## 數據集資訊
本模型的主要訓練數據集是來自Roboflow的[建築工地安全影像數據集](https://www.kaggle.com/datasets/snehilsanyal/construction-site-safety-image-dataset-roboflow/data)。我們對這個數據集進行了額外的標註，並已在Roboflow上公開。增強後的數據集可在此處找到：[建築工地危險檢測於Roboflow](https://universe.roboflow.com/side-projects/construction-hazard-detection)。此數據集包含以下標籤：

- `0: '安全帽'`
- `1: '口罩'`
- `2: '無安全帽'`
- `3: '無口罩'`
- `4: '無安全背心'`
- `5: '人員'`
- `6: '安全錐'`
- `7: '安全背心'`
- `8: '機械設備'`
- `9: '車輛'`

我們全面的數據集確保模型能夠有效識別建築環境中常見的各種潛在危險。

## 安裝指南
按照以下步驟設置此項目：
1. 克隆存儲庫：
   ```
   git clone https://github.com/yihong1120/Construction-Hazard-Detection.git
   ```
2. 導航至項目目錄：
   ```
   cd Construction-Hazard-Detection
   ```
3. 安裝所需依賴項：
   ```
   pip install -r requirements.txt
   ```

## 使用方法

該系統設計用於即時檢測和警告工地上的危險。按照以下詳細步驟有效使用系統：

### 準備環境
1. **設置硬件**：確保你有一台處理能力足夠的電腦和高質量的攝像頭，用於捕捉工地的實時畫面。

2. **安裝攝像頭**：將攝像頭策略性地放置在處理重物和鋼管的高風險區域。

### 訓練模型
1. **收集數據**：收集工地的圖像或視頻，專注於各種類型的危險，如重物、鋼管和人員存在。

2. **數據標註**：對收集到的數據進行標註，準確識別和標記危險和人物形象。

3. **訓練 YOLOv8**：使用標註的數據集訓練 YOLOv8 模型。可以使用以下命令：
   ```
   python train.py --img 640 --batch 16 --epochs 50 --data dataset.yaml --weights yolov8n.pt
   ```
   根據你的數據集和硬件能力調整參數。

### 後處理和部署
1. **應用後處理**：訓練後，應用後處理技術以提高模型在區分危險和非危險條件的準確性。

2. **模型整合**：將訓練好的模型與能夠處理攝像頭實時畫面的軟件整合。

3. **運行系統**：使用以下命令啟動系統：
   ```
   python detect.py --source 0 --weights best.pt --conf-thres 0.4
   ```
   此命令將使用你的攝像頭畫面啟動檢測過程（`--source 0` 指的是默認攝像頭；如有需要，請更改）。`--weights` 選項應指向你訓練的模型，`--conf-thres` 設置檢測的信心閾值。

### 即時監控和警報
1. **監控**：系統將持續分析工地的實時畫面，檢測任何潛在危險。

2. **警報**：當系統檢測到人員處於危險條件下時，將觸發警報。確保有機制（如連接的警報或通知系統）立即通知現場人員。

## 部署指南

要使用 Docker 部署「建築工地危險偵測」系統，請遵循以下步驟：

### 建立 Docker 映像檔
1. 確保您的機器已安裝並正在運行 Docker Desktop。
2. 打開終端機，並導航至克隆儲存庫的根目錄。
3. 使用以下命令建立 Docker 映像檔：
   ```
   docker build -t construction-hazard-detection .
   ```

### 運行 Docker 容器
1. 映像檔建立完成後，您可以使用以下命令來運行容器：
   ```
   docker run -p 8080:8080 -e LINE_TOKEN=your_actual_token construction-hazard-detection
   ```
   將 `your_actual_token` 替換為您實際的 LINE Notify 令牌。

   此命令將啟動容器並對外開放 8080 端口，讓您可以透過主機在 `http://localhost:8080` 訪問應用程式。

### 注意事項
- 確保 `Dockerfile` 存在於專案的根目錄中，並根據您的應用程式需求正確配置。
- `-e LINE_TOKEN=your_actual_token` 旗標在容器內設定了 `LINE_TOKEN` 環境變數，這對於應用程式發送通知是必要的。如果您有其他環境變數，也可以以類似的方式添加。
- `-p 8080:8080` 旗標將容器的 8080 端口映射到主機的 8080 端口，允許您透過主機的 IP 地址和端口號訪問應用程式。

有關 Docker 使用和命令的更多資訊，請參閱 [Docker 文件](https://docs.docker.com/)。

## 貢獻
我們歡迎對此項目的貢獻。請按照以下步驟操作：
1. Fork 存儲庫。
2. 進行你的更改。
3. 提交一個清晰描述你改進的 pull request。

## 開發路線圖
- [x] 數據收集和預處理。
- [ ] 使用工地數據訓練 YOLOv8 模型。
- [ ] 開發後處理技術以提高準確性。
- [ ] 實施即時分析和警報系統。
- [ ] 在模擬環境中進行測試和驗證。
- [ ] 在實際工地進行現場測試部署。
- [ ] 根據用戶反饋進行持續維護和更新。

## 許可證
該項目根據 [AGPL-3.0 許可證](LICENSE.md) 授權。
