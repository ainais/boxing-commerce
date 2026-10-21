package com.ainais.boxing.common;

/** 모든 오류 응답의 공통 형태 */
public record ApiError(String code, String message) {
}
