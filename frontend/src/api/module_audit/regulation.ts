import request from "@/utils/request";

const API_PATH = "/audit/regulation";

const AuditRegulationAPI = {
  listRegulation(query: AuditRegulationPageQuery) {
    return request<ApiResponse<PageResult<AuditRegulationTable[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  detailRegulation(id: number) {
    return request<ApiResponse<AuditRegulationTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  uploadRegulation(payload: AuditRegulationUploadForm) {
    const formData = new FormData();
    if (payload.regulation_name) {
      formData.append("regulation_name", payload.regulation_name);
    }
    if (payload.description) {
      formData.append("description", payload.description);
    }
    const file = payload.file;
    const ext = file.name.split(".").pop()?.toLowerCase() || "txt";
    formData.append("file_type", ext);
    formData.append("file", file);
    return request<ApiResponse>({
      url: `${API_PATH}/upload`,
      method: "post",
      data: formData,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  deleteRegulation(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: { ids },
    });
  },

  optionRegulation() {
    return request<ApiResponse<AuditRegulationOption[]>>({
      url: `${API_PATH}/options`,
      method: "get",
    });
  },
};

export default AuditRegulationAPI;

export interface AuditRegulationPageQuery extends PageQuery {
  keyword?: string;
}

export interface AuditRegulationTable extends BaseType {
  regulation_name: string;
  file_name: string;
  file_type: string;
  file_path?: string;
  file_size?: number;
  status?: string;
  description?: string;
  created_time?: string;
  updated_time?: string;
}

export interface AuditRegulationUploadForm {
  regulation_name?: string;
  description?: string;
  file: File;
}

export interface AuditRegulationOption {
  id: number;
  regulation_name: string;
  file_name: string;
  file_type: string;
  file_size?: number;
  updated_time?: string;
}
