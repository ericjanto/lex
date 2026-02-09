#!/bin/bash
# Quick deployment script for headless Anki on Google Cloud

set -e

PROJECT_ID="lex-anki-server"
INSTANCE_NAME="anki-server"
ZONE="europe-west3-c"

echo "🚀 Deploying Headless Anki to Google Cloud..."

# Create project
echo "📦 Creating GCP project..."
gcloud projects create $PROJECT_ID --name="Lex Anki Server" || echo "Project already exists"
gcloud config set project $PROJECT_ID

# Enable APIs
echo "🔌 Enabling Compute Engine API..."
gcloud services enable compute.googleapis.com

# Create instance
echo "💻 Creating e2-micro instance..."
gcloud compute instances create $INSTANCE_NAME \
  --zone=$ZONE \
  --machine-type=e2-micro \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --tags=anki-server \
  --metadata=startup-script='#!/bin/bash
docker run -d \
  --name anki-headless \
  --restart=always \
  -p 8765:8765 \
  -p 5900:5900 \
  -e ANKICONNECT_WILDCARD_ORIGIN=1 \
  -e VNC_PASSWORD=lex_anki_2026 \
  -v anki_data:/data \
  thisisnttheway/headless-anki:latest
'

# Configure firewall
echo "🔥 Configuring firewall..."
gcloud compute firewall-rules create allow-anki \
  --allow=tcp:8765 \
  --target-tags=anki-server \
  --description="Allow AnkiConnect access" || echo "Firewall rule already exists"

# Get external IP
echo "🌐 Getting external IP..."
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Wait ~2 minutes for the container to start"
echo "2. Update your .env file:"
echo "   ANKI_URL=http://$EXTERNAL_IP:8765"
echo ""
echo "3. Test the connection:"
echo "   curl http://$EXTERNAL_IP:8765 -X POST -d '{\"action\":\"version\",\"version\":6}'"
echo ""
echo "4. For initial AnkiWeb login (one-time):"
echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE -- -L 5900:localhost:5900"
echo "   Then connect VNC to localhost:5900"
